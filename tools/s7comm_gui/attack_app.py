"""S7comm attack scenarios GUI — SSH vào máy Attacker, chạy script tới PLC."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from .attacks import SCENARIO_BY_ID, SCENARIOS
from .config import (
    DEFAULT_ATTACKER_HOST,
    DEFAULT_ATTACKER_PASSWORD,
    DEFAULT_ATTACKER_USER,
    DEFAULT_PLC_IP,
    DEFAULT_RACK,
    DEFAULT_SLOT,
)
from .runner import RemoteRunner
from .theme import (
    ACCENT,
    ACCENT_DARK,
    BG,
    BORDER,
    CATEGORY_COLORS,
    LOG_BG,
    LOG_FG,
    SURFACE,
    SURFACE_ELEVATED,
    TEXT,
    TEXT_MUTED,
    apply_theme,
    mono_font,
)


def _scenario_category(scenario_id: str) -> str:
    if scenario_id.startswith("recon"):
        return "recon"
    if scenario_id.startswith("write"):
        return "write"
    if scenario_id.startswith("dos"):
        return "dos"
    if scenario_id.startswith("malformed"):
        return "malformed"
    return "control"


class AttackApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("S7comm Lab — Attack Tool")
        self.geometry("1080x720")
        self.minsize(900, 600)

        apply_theme(self)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status, style="Status.TLabel", anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 8)
        )
        self.after(120, self._poll_queues)

    def _build_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=16, pady=(12, 8))
        ttk.Label(header, text="S7comm Attack Tool", style="Title.TLabel").pack(side=tk.LEFT)

        conn_outer = ttk.Frame(self, style="Card.TFrame", padding=1)
        conn_outer.pack(fill=tk.X, padx=16, pady=(0, 8))
        conn = ttk.Frame(conn_outer, style="Card.TFrame", padding=(12, 10))
        conn.pack(fill=tk.X)

        plc_row = ttk.Frame(conn, style="Card.TFrame")
        plc_row.pack(fill=tk.X, pady=(0, 8))
        self._badge(plc_row, "PLC", ACCENT).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(plc_row, text="IP", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.plc_ip = tk.StringVar(value=DEFAULT_PLC_IP)
        ttk.Entry(plc_row, textvariable=self.plc_ip, width=14).pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(plc_row, text="Rack", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.rack = tk.IntVar(value=DEFAULT_RACK)
        ttk.Spinbox(plc_row, from_=0, to=7, textvariable=self.rack, width=4).pack(side=tk.LEFT, padx=6)
        ttk.Label(plc_row, text="Slot", style="CardMuted.TLabel").pack(side=tk.LEFT, padx=(10, 0))
        self.slot = tk.IntVar(value=DEFAULT_SLOT)
        ttk.Spinbox(plc_row, from_=0, to=31, textvariable=self.slot, width=4).pack(side=tk.LEFT, padx=6)
        ttk.Button(plc_row, text="Kiểm tra :102", style="Ghost.TButton", command=self._probe_plc).pack(
            side=tk.RIGHT
        )

        atk_row = ttk.Frame(conn, style="Card.TFrame")
        atk_row.pack(fill=tk.X)
        self._badge(atk_row, "Attacker", "#dc2626").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(atk_row, text="Host", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.attacker_host = tk.StringVar(value=DEFAULT_ATTACKER_HOST)
        ttk.Entry(atk_row, textvariable=self.attacker_host, width=14).pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(atk_row, text="User", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.attacker_user = tk.StringVar(value=DEFAULT_ATTACKER_USER)
        ttk.Entry(atk_row, textvariable=self.attacker_user, width=10).pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(atk_row, text="Pass", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.attacker_pass = tk.StringVar(value=DEFAULT_ATTACKER_PASSWORD)
        ttk.Entry(atk_row, textvariable=self.attacker_pass, width=10, show="•").pack(side=tk.LEFT, padx=6)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        left_outer = ttk.Frame(body, style="Card.TFrame", width=360)
        body.add(left_outer, weight=2)
        left = ttk.Frame(left_outer, style="Card.TFrame", padding=10)
        left.pack(fill=tk.BOTH, expand=True)

        ttk.Label(left, text="Kịch bản tấn công", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))

        list_frame = ttk.Frame(left, style="Card.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True)

        scroll_canvas = tk.Canvas(list_frame, bg=SURFACE, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_inner = ttk.Frame(scroll_canvas, style="Card.TFrame")
        scroll_window = scroll_canvas.create_window((0, 0), window=scroll_inner, anchor=tk.NW)

        def _on_inner_configure(_event=None) -> None:
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_canvas_configure(event) -> None:
            scroll_canvas.itemconfig(scroll_window, width=event.width)

        def _on_mousewheel(event) -> None:
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(_event=None) -> None:
            scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(_event=None) -> None:
            scroll_canvas.unbind_all("<MouseWheel>")

        scroll_inner.bind("<Configure>", _on_inner_configure)
        scroll_canvas.bind("<Configure>", _on_canvas_configure)
        scroll_canvas.bind("<Enter>", _bind_mousewheel)
        scroll_canvas.bind("<Leave>", _unbind_mousewheel)

        for sc in SCENARIOS:
            cat = _scenario_category(sc.id)
            self._scenario_row(scroll_inner, sc.id, sc.name, sc.description, cat)

        run_box = ttk.Frame(left, style="Card.TFrame")
        run_box.pack(fill=tk.X, pady=(10, 0))
        btn_row = ttk.Frame(run_box, style="Card.TFrame")
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Dừng", style="Danger.TButton", command=self._stop_worker).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4)
        )
        ttk.Button(btn_row, text="Xóa log", style="Ghost.TButton", command=self._clear_logs).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )

        right_outer = ttk.Frame(body, style="Card.TFrame")
        body.add(right_outer, weight=3)
        right = ttk.Frame(right_outer, style="Card.TFrame", padding=10)
        right.pack(fill=tk.BOTH, expand=True)
        ttk.Label(right, text="Log thực thi", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 6))

        log_frame = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.attack_log = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=mono_font(),
            bg=LOG_BG,
            fg=LOG_FG,
            insertbackground=LOG_FG,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=8,
        )
        self.attack_log.pack(fill=tk.BOTH, expand=True)
        self.attack_log.configure(state=tk.DISABLED)

    def _badge(self, parent: tk.Misc, text: str, color: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI Semibold", 9),
            fg="#ffffff",
            bg=color,
            padx=8,
            pady=3,
        )

    def _scenario_row(
        self, parent: tk.Misc, sid: str, name: str, description: str, category: str
    ) -> None:
        color = CATEGORY_COLORS.get(category, ACCENT)
        outer = tk.Frame(parent, bg=SURFACE, pady=3)
        outer.pack(fill=tk.X)

        card = tk.Frame(outer, bg=SURFACE_ELEVATED, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill=tk.X, padx=2)

        stripe = tk.Frame(card, bg=color, width=4)
        stripe.pack(side=tk.LEFT, fill=tk.Y)

        content = tk.Frame(card, bg=SURFACE_ELEVATED, padx=8, pady=6)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top = tk.Frame(content, bg=SURFACE_ELEVATED)
        top.pack(fill=tk.X)
        tk.Label(
            top,
            text=name,
            font=("Segoe UI Semibold", 10),
            fg=TEXT,
            bg=SURFACE_ELEVATED,
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        run_btn = tk.Button(
            top,
            text="Chạy",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg=ACCENT,
            activeforeground="#ffffff",
            activebackground=ACCENT_DARK,
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=lambda s=sid: self._run_selected([s]),
        )
        run_btn.pack(side=tk.RIGHT)

        tk.Label(
            content,
            text=description,
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=SURFACE_ELEVATED,
            anchor=tk.W,
            wraplength=280,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(2, 0))

    def _append_log(self, line: str) -> None:
        self.attack_log.configure(state=tk.NORMAL)
        self.attack_log.insert(tk.END, line + "\n")
        self.attack_log.see(tk.END)
        self.attack_log.configure(state=tk.DISABLED)

    def _log(self, msg: str) -> None:
        self.log_queue.put(msg)

    def _poll_queues(self) -> None:
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(msg)
        self.after(120, self._poll_queues)

    def _get_runner(self) -> RemoteRunner:
        return RemoteRunner(
            self.attacker_host.get().strip(),
            self.attacker_user.get().strip(),
            self.attacker_pass.get(),
            self._log,
        )

    def _busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def _set_status(self, text: str) -> None:
        self.status.set(text)

    def _run_bg(self, fn) -> None:
        if self._busy():
            messagebox.showwarning("Đang chạy", "Đợi tác vụ hiện tại kết thúc hoặc bấm Dừng.")
            return
        self.cancel_event.clear()

        def wrapper() -> None:
            try:
                fn()
            except Exception as e:
                self._log(f"[ERROR] {e!r}")
            finally:
                self._set_status("")

        self.worker = threading.Thread(target=wrapper, daemon=True)
        self.worker.start()

    def _probe_plc(self) -> None:
        def job() -> None:
            self._set_status("Kiểm tra PLC từ Attacker ...")
            runner = self._get_runner()
            plc = self.plc_ip.get().strip()
            ok = runner.probe_plc(plc)
            self._log(f"[Attacker→PLC] {plc}:102 → {'OPEN' if ok else 'CLOSED/FAIL'}")
            runner.close()

        self._run_bg(job)

    def _run_selected(self, scenario_ids: list[str]) -> None:
        def job() -> None:
            runner = self._get_runner()
            plc = self.plc_ip.get().strip()
            rack = self.rack.get()
            slot = self.slot.get()
            self._set_status(f"SSH Attacker — chạy {len(scenario_ids)} kịch bản ...")
            for sid in scenario_ids:
                if self.cancel_event.is_set():
                    self._log("[STOP] Aborted.")
                    break
                runner.run_scenario(SCENARIO_BY_ID[sid], plc, rack, slot, cancel=self.cancel_event)
            runner.close()

        self._run_bg(job)

    def _stop_worker(self) -> None:
        self.cancel_event.set()
        self._log("[STOP] Cancel signal sent.")

    def _clear_logs(self) -> None:
        self.attack_log.configure(state=tk.NORMAL)
        self.attack_log.delete("1.0", tk.END)
        self.attack_log.configure(state=tk.DISABLED)


def main() -> None:
    try:
        AttackApp().mainloop()
    except Exception:
        import traceback
        from pathlib import Path

        log = Path(__file__).resolve().parent / "launch_errors.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
        raise


if __name__ == "__main__":
    main()
