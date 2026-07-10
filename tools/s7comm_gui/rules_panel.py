"""Suricata rules viewer and alert monitor for the lab GUI."""
from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk

from .config import (
    CAPTURE_IFACE,
    CONTROL_NET,
    EXTERNAL_NET,
    RULE_FILES,
    SUPERVISOR_NET,
    SURICATA_FAST_LOG,
)
from .rules_parser import SuricataRule, load_all_rules, rule_stats
from .theme import LOG_BG, LOG_FG, mono_font
from .traffic import SuricataMonitor


class RulesPanel(ttk.Frame):
    def __init__(
        self,
        master,
        get_ids_host,
        get_ids_user,
        get_ids_pass,
        on_log,
        on_status,
    ) -> None:
        super().__init__(master)
        self.get_ids_host = get_ids_host
        self.get_ids_user = get_ids_user
        self.get_ids_pass = get_ids_pass
        self.on_log = on_log
        self.on_status = on_status

        self.rules_by_file: dict[str, list[SuricataRule]] = {}
        self.selected_rule: SuricataRule | None = None
        self.suricata_monitor: SuricataMonitor | None = None

        self._build()
        self.reload_rules()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=4)

        cfg = ttk.LabelFrame(top, text="Lab network", padding=6)
        cfg.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(cfg, text="CONTROL_NET").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.control_net = tk.StringVar(value=CONTROL_NET)
        ttk.Entry(cfg, textvariable=self.control_net, width=20).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(cfg, text="SUPERVISOR_NET").grid(row=0, column=2, sticky=tk.W, padx=(8, 4))
        self.supervisor_net = tk.StringVar(value=SUPERVISOR_NET)
        ttk.Entry(cfg, textvariable=self.supervisor_net, width=20).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(cfg, text="EXTERNAL_NET").grid(row=1, column=0, sticky=tk.W, padx=4)
        self.external_net = tk.StringVar(value=EXTERNAL_NET)
        ttk.Entry(cfg, textvariable=self.external_net, width=20).grid(row=1, column=1, sticky=tk.W)
        ttk.Label(cfg, text="Interface").grid(row=1, column=2, sticky=tk.W, padx=(8, 4))
        self.capture_iface = tk.StringVar(value=CAPTURE_IFACE)
        ttk.Entry(cfg, textvariable=self.capture_iface, width=8).grid(row=1, column=3, sticky=tk.W)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill=tk.X, pady=2)
        ttk.Button(toolbar, text="Reload", command=self.reload_rules).pack(side=tk.LEFT, padx=2)

        self.stats_label = ttk.Label(top, text="", font=("", 9))
        self.stats_label.pack(anchor=tk.W, pady=(0, 2))

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(body)
        body.add(left, weight=2)

        filter_row = ttk.Frame(left)
        filter_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(filter_row, text="Filter:").pack(side=tk.LEFT)
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

        rule_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(rule_tab, text="Rule detail")

        detail = ttk.LabelFrame(rule_tab, text="Details", padding=4)
        detail.pack(fill=tk.X, padx=4, pady=4)
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

        self.rule_view = scrolledtext.ScrolledText(
            rule_tab, wrap=tk.NONE, font=mono_font(), state=tk.DISABLED
        )
        self.rule_view.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.alert_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.alert_tab, text="Alerts")
        self.main_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        path_row = ttk.Frame(self.alert_tab)
        path_row.pack(fill=tk.X, padx=4, pady=(4, 0))
        ttk.Label(path_row, text="Alert log:").pack(side=tk.LEFT)
        self.alert_log_path = tk.StringVar(value=SURICATA_FAST_LOG)
        ttk.Entry(path_row, textvariable=self.alert_log_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )
        alert_btns = ttk.Frame(self.alert_tab)
        alert_btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(alert_btns, text="Clear log", command=self._clear_alert_log).pack(side=tk.LEFT, padx=2)
        self.alert_log = scrolledtext.ScrolledText(
            self.alert_tab, wrap=tk.WORD, font=mono_font(),
            bg=LOG_BG, fg=LOG_FG, relief=tk.SUNKEN, borderwidth=1,
        )
        self.alert_log.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

    def _set_rule_text(self, text: str) -> None:
        self.rule_view.config(state=tk.NORMAL)
        self.rule_view.delete("1.0", tk.END)
        if text:
            self.rule_view.insert("1.0", text)
        self.rule_view.config(state=tk.DISABLED)

    def _log_alert(self, msg: str) -> None:
        self.alert_log.insert(tk.END, msg + "\n")
        self.alert_log.see(tk.END)

    def _clear_alert_log(self) -> None:
        self.alert_log.delete("1.0", tk.END)

    def _on_tab_changed(self, _event=None) -> None:
        tab = self.main_notebook.select()
        if tab == str(self.alert_tab):
            self._start_alerts()
        else:
            self._stop_alerts()

    def _start_alerts(self) -> None:
        if self.suricata_monitor and self.suricata_monitor.running:
            return
        log_path = self.alert_log_path.get().strip() or SURICATA_FAST_LOG
        self.suricata_monitor = SuricataMonitor(
            self.get_ids_host(),
            self.get_ids_user(),
            self.get_ids_pass(),
            self._log_alert,
            self.on_status,
            log_path=log_path,
            tail_lines=0,
        )
        self.suricata_monitor.start(filter_s7=True)
        self.on_status(f"Following new alerts: {log_path}")

    def _stop_alerts(self) -> None:
        if self.suricata_monitor:
            self.suricata_monitor.stop()
            self.suricata_monitor = None

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
                self._set_rule_text(rule.raw)
                return
