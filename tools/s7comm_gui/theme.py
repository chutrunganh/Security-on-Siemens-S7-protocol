"""Shared tkinter/ttk styling — standard desktop look."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

BG = "#f0f0f0"
SURFACE = "#ffffff"
BORDER = "#aca899"
TEXT = "#000000"
TEXT_MUTED = "#444444"

LOG_BG = "#ffffff"
LOG_FG = "#000000"

FONT_UI = ("Segoe UI", 9)
FONT_UI_BOLD = ("Segoe UI", 9, "bold")
FONT_TITLE = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 9)


def mono_font() -> tuple[str, int]:
    try:
        tkfont.Font(family="Consolas", size=9)
        return FONT_MONO
    except tk.TclError:
        return ("Courier New", 9)


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    style.configure(".", background=BG, foreground=TEXT, font=FONT_UI)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=TEXT_MUTED, font=FONT_UI)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Header.TLabel", background=SURFACE, foreground=TEXT, font=FONT_UI_BOLD)
    style.configure(
        "Status.TLabel",
        background=BG,
        foreground=TEXT_MUTED,
        relief=tk.SUNKEN,
        padding=(6, 3),
        font=FONT_UI,
    )
    style.configure("TPanedwindow", background=BG)
    return style
