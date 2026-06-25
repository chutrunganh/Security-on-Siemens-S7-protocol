"""Suricata rules management panel for the lab GUI."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from .config import CAPTURE_IFACE, HOME_NET, RULE_FILES
from .rules_parser import (
    SuricataRule,
    load_all_rules,
    read_file_content,
    rule_stats,
    save_file_content,
    save_rule,
)
from .suricata_deploy import SuricataDeployer
from .theme import BG, LOG_BG, LOG_FG, mono_font
from .traffic import SuricataMonitor, TcpdumpMonitor


class RulesPanel(ttk.Frame):
    def __init__(
        self,
        master,
        get_ids_host,
        get_ids_user,
        get_ids_pass,
        get_plc_ip,
        on_log,
        on_status,
        is_busy,
        run_bg,
    ) -> None:
        super().__init__(master)
        self.get_ids_host = get_ids_host
        self.get_ids_user = get_ids_user
        self.get_ids_pass = get_ids_pass
        self.get_plc_ip = get_plc_ip
        self.on_log = on_log
        self.on_status = on_status
        self.is_busy = is_busy
        self.run_bg = run_bg

        self.rules_by_file: dict[str, list[SuricataRule]] = {}
        self.selected_rule: SuricataRule | None = None
        self.file_mode = tk.BooleanVar(value=False)
        self.suricata_monitor: SuricataMonitor | None = None

        self._build()
        self.reload_rules()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=4)

        cfg = ttk.LabelFrame(top, text="Cấu hình Suricata", padding=6)
        cfg.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(cfg, text="HOME_NET").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.home_net = tk.StringVar(value=HOME_NET)
        ttk.Entry(cfg, textvariable=self.home_net, width=44).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(cfg, text="Interface").grid(row=0, column=2, sticky=tk.W, padx=(8, 4))
        self.capture_iface = tk.StringVar(value=CAPTURE_IFACE)
        ttk.Entry(cfg, textvariable=self.capture_iface, width=8).grid(row=0, column=3, sticky=tk.W)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill=tk.X, pady=2)
        for text, cmd in (
            ("Tải lại", self.reload_rules),
            ("Lưu luật", self.save_current_rule),
            ("Lưu file", self.save_whole_file),
            ("Deploy luật", self.deploy_rules_only),
            ("Deploy + yaml", self.deploy_full),
            ("Validate", self.validate_remote),
            ("Trạng thái", self.fetch_status),
        ):
            ttk.Button(toolbar, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        self.stats_label = ttk.Label(top, text="", font=("", 9))
        self.stats_label.pack(anchor=tk.W, pady=(0, 2))

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(body)
        body.add(left, weight=2)

        filter_row = ttk.Frame(left)
        filter_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(filter_row, text="Lọc:").pack(side=tk.LEFT)
        self.filter_text = tk.StringVar()
        self.filter_text.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(filter_row, textvariable=self.filter_text, width=24).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        tree_wrap = ttk.Frame(left)
        tree_wrap.pack(fill=tk.BOTH, expand=True)
        cols = ("sid", "msg", "attack", "pri", "on")
        self.tree = ttk.Treeview(tree_wrap, columns=cols, show="tree headings", height=14)
        self.tree.heading("#0", text="File / SID")
        self.tree.heading("sid", text="SID")
        self.tree.heading("msg", text="Message")
        self.tree.heading("attack", text="Attack")
        self.tree.heading("pri", text="Pri")
        self.tree.heading("on", text="On")
        self.tree.column("#0", width=110)
        self.tree.column("sid", width=64)
        self.tree.column("msg", width=200)
        self.tree.column("attack", width=90)
        self.tree.column("pri", width=36)
        self.tree.column("on", width=28)
        yscroll = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        right = ttk.Frame(body)
        body.add(right, weight=3)

        self.main_notebook = ttk.Notebook(right)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1 — Soạn luật
        rule_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(rule_tab, text="Soạn luật")

        mode_row = ttk.Frame(rule_tab)
        mode_row.pack(fill=tk.X, padx=4, pady=4)
        ttk.Checkbutton(
            mode_row,
            text="Sửa cả file .rules",
            variable=self.file_mode,
            command=self._toggle_edit_mode,
        ).pack(side=tk.LEFT)
        ttk.Label(mode_row, text="File:").pack(side=tk.LEFT, padx=(10, 2))
        self.file_choice = tk.StringVar(value=RULE_FILES[0])
        self.file_combo = ttk.Combobox(
            mode_row, textvariable=self.file_choice, values=list(RULE_FILES), width=20, state="readonly"
        )
        self.file_combo.pack(side=tk.LEFT)
        self.file_combo.bind("<<ComboboxSelected>>", lambda e: self._load_file_editor())

        detail = ttk.LabelFrame(rule_tab, text="Chi tiết", padding=4)
        detail.pack(fill=tk.X, padx=4, pady=(0, 4))
        self.detail_sid = tk.StringVar(value="—")
        self.detail_msg = tk.StringVar(value="—")
        self.detail_attack = tk.StringVar(value="—")
        ttk.Label(detail, text="SID:").grid(row=0, column=0, sticky=tk.W, padx=4)
        ttk.Label(detail, textvariable=self.detail_sid).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(detail, text="Attack:").grid(row=0, column=2, sticky=tk.W, padx=4)
        ttk.Label(detail, textvariable=self.detail_attack).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(detail, text="Message:").grid(row=1, column=0, sticky=tk.W, padx=4)
        ttk.Label(detail, textvariable=self.detail_msg, wraplength=480).grid(
            row=1, column=1, columnspan=3, sticky=tk.W
        )

        self.rule_editor = scrolledtext.ScrolledText(rule_tab, wrap=tk.NONE, font=mono_font())
        self.rule_editor.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Tab 2 — Deploy log
        deploy_tab = tk.Frame(self.main_notebook, bg=BG)
        self.main_notebook.add(deploy_tab, text="Deploy log")
        self.deploy_log = scrolledtext.ScrolledText(
            deploy_tab, wrap=tk.WORD, font=mono_font(),
            bg=LOG_BG, fg=LOG_FG, insertbackground=LOG_FG, relief=tk.FLAT,
        )
        self.deploy_log.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tab 3 — Alert Suricata
        alert_tab = tk.Frame(self.main_notebook, bg=BG)
        self.main_notebook.add(alert_tab, text="Alert Suricata")
        alert_btns = ttk.Frame(alert_tab)
        alert_btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(alert_btns, text="Bắt alert", style="Accent.TButton", command=self._start_alerts).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(alert_btns, text="Dừng", style="Ghost.TButton", command=self._stop_alerts).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(alert_btns, text="Tcpdump :102", style="Ghost.TButton", command=self._tcpdump_snapshot).pack(
            side=tk.LEFT, padx=2
        )
        self.alert_log = scrolledtext.ScrolledText(
            alert_tab, wrap=tk.WORD, font=mono_font(),
            bg=LOG_BG, fg=LOG_FG, insertbackground=LOG_FG, relief=tk.FLAT,
        )
        self.alert_log.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

    def _log_alert(self, msg: str) -> None:
        self.alert_log.insert(tk.END, msg + "\n")
        self.alert_log.see(tk.END)

    def _start_alerts(self) -> None:
        if self.suricata_monitor and self.suricata_monitor.running:
            return
        self.main_notebook.select(2)
        self.suricata_monitor = SuricataMonitor(
            self.get_ids_host(),
            self.get_ids_user(),
            self.get_ids_pass(),
            self._log_alert,
            self.on_status,
        )
        self.suricata_monitor.start(filter_s7=True)
        self.on_status(f"Đang đọc alert trên {self.get_ids_host()} ...")

    def _stop_alerts(self) -> None:
        if self.suricata_monitor:
            self.suricata_monitor.stop()
        self._log_alert("[IDS] Dừng đọc alert.")

    def _tcpdump_snapshot(self) -> None:
        mon = TcpdumpMonitor(
            self.get_ids_host(),
            self.get_ids_user(),
            self.get_ids_pass(),
            self.get_plc_ip(),
            self._log_alert,
            self._log_alert,
        )

        def job() -> None:
            self.on_status(f"Tcpdump trên IDS {self.get_ids_host()} ...")
            mon.start(count=40)

        threading.Thread(target=job, daemon=True).start()

    def _log_deploy(self, msg: str) -> None:
        self.deploy_log.insert(tk.END, msg + "\n")
        self.deploy_log.see(tk.END)
        self.on_log(f"[Rules] {msg}")

    def _deployer(self) -> SuricataDeployer:
        return SuricataDeployer(
            self.get_ids_host(),
            self.get_ids_user(),
            self.get_ids_pass(),
            self._log_deploy,
        )

    def reload_rules(self) -> None:
        self.rules_by_file = load_all_rules()
        self.stats_label.config(text=rule_stats(self.rules_by_file))
        self._populate_tree()
        self.on_log("[Rules] Reloaded local rule files.")

    def _populate_tree(self, filter_q: str = "") -> None:
        q = filter_q.strip().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fname in RULE_FILES:
            rules = self.rules_by_file.get(fname, [])
            parent = self.tree.insert("", tk.END, iid=f"file:{fname}", text=fname, open=True)
            shown = 0
            for rule in rules:
                hay = f"{rule.sid} {rule.msg} {rule.attack}".lower()
                if q and q not in hay:
                    continue
                iid = f"{fname}:{rule.line_no}"
                self.tree.insert(
                    parent,
                    tk.END,
                    iid=iid,
                    text=rule.sid,
                    values=(rule.sid, rule.msg[:48], rule.attack[:20], rule.priority, "Y" if rule.enabled else "N"),
                )
                shown += 1
            self.tree.item(parent, text=f"{fname} ({shown})")

    def _apply_filter(self) -> None:
        self._populate_tree(self.filter_text.get())

    def _on_tree_select(self, _event=None) -> None:
        if self.file_mode.get():
            return
        sel = self.tree.selection()
        if not sel or sel[0].startswith("file:"):
            self.selected_rule = None
            return
        fname, line_s = sel[0].split(":", 1)
        line_no = int(line_s)
        for rule in self.rules_by_file.get(fname, []):
            if rule.line_no == line_no:
                self.selected_rule = rule
                self.detail_sid.set(rule.sid)
                self.detail_msg.set(rule.msg)
                self.detail_attack.set(rule.attack or rule.protocol or "—")
                self.rule_editor.delete("1.0", tk.END)
                self.rule_editor.insert("1.0", rule.raw)
                return

    def _toggle_edit_mode(self) -> None:
        if self.file_mode.get():
            self._load_file_editor()
        elif self.selected_rule:
            self.rule_editor.delete("1.0", tk.END)
            self.rule_editor.insert("1.0", self.selected_rule.raw)

    def _load_file_editor(self) -> None:
        name = self.file_choice.get()
        self.rule_editor.delete("1.0", tk.END)
        self.rule_editor.insert("1.0", read_file_content(name))
        self.on_log(f"[Rules] Loaded file {name} for editing.")

    def save_current_rule(self) -> None:
        if self.file_mode.get():
            messagebox.showinfo("Lưu", "Đang ở chế độ sửa cả file — dùng 'Lưu cả file'.")
            return
        if not self.selected_rule:
            messagebox.showinfo("Lưu", "Chọn một luật trong cây bên trái.")
            return
        new_raw = self.rule_editor.get("1.0", tk.END).strip()
        if not new_raw.startswith("alert "):
            messagebox.showerror("Lỗi", "Dòng phải bắt đầu bằng 'alert '")
            return
        self.selected_rule.raw = new_raw
        save_rule(self.selected_rule)
        self.reload_rules()
        messagebox.showinfo("Lưu", f"Đã lưu SID {self.selected_rule.sid} vào {self.selected_rule.file_name}")

    def save_whole_file(self) -> None:
        name = self.file_choice.get() if self.file_mode.get() else (
            self.selected_rule.file_name if self.selected_rule else RULE_FILES[0]
        )
        content = self.rule_editor.get("1.0", tk.END)
        save_file_content(name, content)
        self.reload_rules()
        messagebox.showinfo("Lưu", f"Đã ghi file detect/rules/{name}")

    def _run_deploy(self, fn, status: str) -> None:
        if self.is_busy():
            messagebox.showwarning("Busy", "Đang có tác vụ khác chạy.")
            return

        self.main_notebook.select(1)
        self.on_status(status)

        def job() -> None:
            try:
                fn()
            except Exception as e:
                self._log_deploy(f"ERROR: {e!r}")

        self.run_bg(job)

    def deploy_rules_only(self) -> None:
        def job() -> None:
            code = self._deployer().deploy_rules_only()
            self._log_deploy(f"Deploy rules finished, exit={code}")

        self._run_deploy(job, "Deploy luật lên IDS ...")

    def deploy_full(self) -> None:
        def job() -> None:
            code = self._deployer().deploy_full(
                self.home_net.get().strip(),
                self.capture_iface.get().strip(),
            )
            self._log_deploy(f"Deploy full finished, exit={code}")

        self._run_deploy(job, "Deploy đầy đủ (rules + yaml) ...")

    def validate_remote(self) -> None:
        def job() -> None:
            code = self._deployer().validate_remote()
            self._log_deploy(f"suricata -T exit={code}")

        self._run_deploy(job, "Validate Suricata trên IDS ...")

    def fetch_status(self) -> None:
        def job() -> None:
            self._deployer().fetch_remote_status()

        self._run_deploy(job, "Đọc trạng thái IDS ...")
