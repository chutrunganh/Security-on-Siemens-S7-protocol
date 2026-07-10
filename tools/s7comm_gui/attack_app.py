"""S7comm attack scenarios GUI — SSH to Attacker VM, run scripts against PLC."""
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
from .theme import BORDER, LOG_BG, LOG_FG, apply_theme, mono_font


class AttackApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("S7comm Lab — Attack Tool")
        self.geometry("900x640")
        self.minsize(780, 520)

        apply_theme(self)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, style="Status.TLabel", anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )
        self.after(120, self._poll_queues)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(8, 8, 8, 4))
        header.pack(fill=tk.X)
        ttk.Label(header, text="S7comm Attack Tool", style="Title.TLabel").pack(side=tk.LEFT)

        conn = ttk.Frame(self, padding=(8, 0))
        conn.pack(fill=tk.X)

        plc = ttk.LabelFrame(conn, text="PLC", padding=8)
        plc.pack(fill=tk.X, pady=(0, 6))
        plc_row = ttk.Frame(plc)
        plc_row.pack(fill=tk.X)
        ttk.Label(plc_row, text="IP").pack(side=tk.LEFT)
        self.plc_ip = tk.StringVar(value=DEFAULT_PLC_IP)
        ttk.Entry(plc_row, textvariable=self.plc_ip, width=14).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(plc_row, text="Rack").pack(side=tk.LEFT)
        self.rack = tk.IntVar(value=DEFAULT_RACK)
        ttk.Spinbox(plc_row, from_=0, to=7, textvariable=self.rack, width=4).pack(side=tk.LEFT, padx=4)
        ttk.Label(plc_row, text="Slot").pack(side=tk.LEFT, padx=(8, 0))
        self.slot = tk.IntVar(value=DEFAULT_SLOT)
        ttk.Spinbox(plc_row, from_=0, to=31, textvariable=self.slot, width=4).pack(side=tk.LEFT, padx=4)
        ttk.Button(plc_row, text="Check :102", command=self._probe_plc).pack(side=tk.RIGHT)

        atk = ttk.LabelFrame(conn, text="Attacker", padding=8)
        atk.pack(fill=tk.X)
        atk_row = ttk.Frame(atk)
        atk_row.pack(fill=tk.X)
        ttk.Label(atk_row, text="Host").pack(side=tk.LEFT)
        self.attacker_host = tk.StringVar(value=DEFAULT_ATTACKER_HOST)
        ttk.Entry(atk_row, textvariable=self.attacker_host, width=14).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(atk_row, text="User").pack(side=tk.LEFT)
        self.attacker_user = tk.StringVar(value=DEFAULT_ATTACKER_USER)
        ttk.Entry(atk_row, textvariable=self.attacker_user, width=10).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(atk_row, text="Password").pack(side=tk.LEFT)
        self.attacker_pass = tk.StringVar(value=DEFAULT_ATTACKER_PASSWORD)
        ttk.Entry(atk_row, textvariable=self.attacker_pass, width=10, show="*").pack(side=tk.LEFT, padx=4)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.LabelFrame(body, text="Attack scenarios", padding=6)
        body.add(left, weight=1)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scroll_canvas = tk.Canvas(list_frame, bg=LOG_BG, highlightthickness=1, highlightbackground=BORDER)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_inner = ttk.Frame(scroll_canvas)
        scroll_window = scroll_canvas.create_window((0, 0), window=scroll_inner, anchor=tk.NW)

        def _on_inner_configure(_event=None) -> None:
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_canvas_configure(event) -> None:
            scroll_canvas.itemconfig(scroll_window, width=event.width)

        def _on_mousewheel(event) -> None:
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scroll_inner.bind("<Configure>", _on_inner_configure)
        scroll_canvas.bind("<Configure>", _on_canvas_configure)
        scroll_canvas.bind("<Enter>", lambda _e: scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scroll_canvas.bind("<Leave>", lambda _e: scroll_canvas.unbind_all("<MouseWheel>"))

        for sc in SCENARIOS:
            self._scenario_row(scroll_inner, sc.id, sc.name)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Stop", command=self._stop_worker).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Clear log", command=self._clear_logs).pack(side=tk.LEFT)

        right = ttk.LabelFrame(body, text="Execution log", padding=6)
        body.add(right, weight=2)

        self.attack_log = scrolledtext.ScrolledText(
            right,
            wrap=tk.WORD,
            font=mono_font(),
            bg=LOG_BG,
            fg=LOG_FG,
            relief=tk.SUNKEN,
            borderwidth=1,
        )
        self.attack_log.pack(fill=tk.BOTH, expand=True)
        self.attack_log.configure(state=tk.DISABLED)

    def _scenario_row(self, parent: tk.Misc, sid: str, name: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=1)
        ttk.Label(row, text=name).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 8))
        ttk.Button(row, text="Run", width=8, command=lambda s=sid: self._run_selected([s])).pack(
            side=tk.RIGHT, padx=2
        )

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
            messagebox.showwarning("Busy", "Wait for the current task to finish or click Stop.")
            return
        self.cancel_event.clear()

        def wrapper() -> None:
            try:
                fn()
            except Exception as e:
                self._log(f"[ERROR] {e!r}")
            finally:
                self._set_status("Ready")

        self.worker = threading.Thread(target=wrapper, daemon=True)
        self.worker.start()

    def _probe_plc(self) -> None:
        def job() -> None:
            self._set_status("Checking PLC from Attacker ...")
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
            self._set_status(f"Running {len(scenario_ids)} scenario(s) via SSH ...")
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
