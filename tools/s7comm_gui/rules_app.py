"""Suricata rules viewer GUI (standalone app)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .config import DEFAULT_IDS_HOST, DEFAULT_IDS_PASSWORD, DEFAULT_IDS_USER, DEFAULT_PLC_IP
from .rules_panel import RulesPanel
from .theme import apply_theme


class RulesApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("S7comm Lab — Suricata Rules Tool")
        self.geometry("1100x680")
        self.minsize(920, 560)

        apply_theme(self)

        self._build_header()
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, style="Status.TLabel", anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 8)
        )

        self.panel = RulesPanel(
            self,
            get_ids_host=lambda: self.ids_host.get().strip(),
            get_ids_user=lambda: self.ids_user.get().strip(),
            get_ids_pass=self.ids_pass.get,
            on_log=self._noop_log,
            on_status=self._set_status,
        )
        self.panel.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

    def _build_header(self) -> None:
        outer = ttk.Frame(self, style="Card.TFrame", padding=1)
        outer.pack(fill=tk.X, padx=16, pady=(12, 4))
        bar = ttk.Frame(outer, style="Card.TFrame", padding=(12, 8))
        bar.pack(fill=tk.X)

        ttk.Label(bar, text="Suricata Rules Tool", style="Title.TLabel").pack(side=tk.LEFT)

        row = ttk.Frame(bar, style="Card.TFrame")
        row.pack(side=tk.RIGHT)
        ttk.Label(row, text="IDS", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.ids_host = tk.StringVar(value=DEFAULT_IDS_HOST)
        ttk.Entry(row, textvariable=self.ids_host, width=13).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(row, text="User", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.ids_user = tk.StringVar(value=DEFAULT_IDS_USER)
        ttk.Entry(row, textvariable=self.ids_user, width=8).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(row, text="Pass", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.ids_pass = tk.StringVar(value=DEFAULT_IDS_PASSWORD)
        ttk.Entry(row, textvariable=self.ids_pass, width=8, show="•").pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(row, text="PLC", style="CardMuted.TLabel").pack(side=tk.LEFT)
        self.plc_ip = tk.StringVar(value=DEFAULT_PLC_IP)
        ttk.Entry(row, textvariable=self.plc_ip, width=13).pack(side=tk.LEFT, padx=4)

    def _noop_log(self, _msg: str) -> None:
        pass

    def _set_status(self, text: str) -> None:
        self.status.set(text)


def main() -> None:
    try:
        RulesApp().mainloop()
    except Exception:
        import traceback
        from pathlib import Path

        log = Path(__file__).resolve().parent / "launch_errors.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
        raise


if __name__ == "__main__":
    main()
