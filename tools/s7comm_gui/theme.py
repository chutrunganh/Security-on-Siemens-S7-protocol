"""Shared light theme for S7comm GUI tools (tkinter/ttk)."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# Palette — light, high contrast for presentation
BG = "#eef1f6"
SURFACE = "#ffffff"
SURFACE_ELEVATED = "#f8fafc"
BORDER = "#cbd5e1"
TEXT = "#0f172a"
TEXT_MUTED = "#64748b"
ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
WARNING = "#d97706"

LOG_BG = "#ffffff"
LOG_FG = "#1e293b"

CATEGORY_COLORS = {
    "recon": "#3b82f6",
    "write": "#ea580c",
    "dos": "#dc2626",
    "malformed": "#9333ea",
    "control": "#ca8a04",
}

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI Semibold", 10)
FONT_TITLE = ("Segoe UI Semibold", 14)
FONT_MONO = ("Cascadia Mono", 10)
FONT_MONO_FALLBACK = ("Consolas", 10)


def mono_font() -> tuple[str, int]:
    try:
        tkfont.Font(family="Cascadia Mono", size=10)
        return FONT_MONO
    except tk.TclError:
        return FONT_MONO_FALLBACK


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT, font=FONT_UI)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE, relief=tk.FLAT)
    style.configure("Elevated.TFrame", background=SURFACE_ELEVATED)

    style.configure(
        "Card.TLabelframe",
        background=SURFACE,
        bordercolor=BORDER,
        relief=tk.GROOVE,
        borderwidth=1,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=SURFACE,
        foreground=TEXT_MUTED,
        font=FONT_UI_BOLD,
    )
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))
    style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=TEXT_MUTED, font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Header.TLabel", background=SURFACE, foreground=TEXT, font=FONT_UI_BOLD)

    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=4,
    )
    style.configure(
        "TSpinbox",
        fieldbackground=SURFACE,
        foreground=TEXT,
        arrowcolor=TEXT_MUTED,
        bordercolor=BORDER,
        padding=2,
    )

    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        focuscolor=ACCENT,
        padding=(12, 6),
        font=FONT_UI_BOLD,
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT_DARK), ("disabled", BORDER)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    style.configure(
        "Ghost.TButton",
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        padding=(10, 5),
    )
    style.map("Ghost.TButton", background=[("active", SURFACE_ELEVATED)])

    style.configure(
        "Danger.TButton",
        background="#fef2f2",
        foreground=DANGER,
        bordercolor="#fecaca",
        padding=(10, 5),
    )
    style.map("Danger.TButton", background=[("active", "#fee2e2")])

    style.configure(
        "Small.TButton",
        background=SURFACE,
        foreground=ACCENT,
        bordercolor=BORDER,
        padding=(8, 3),
        font=("Segoe UI", 9),
    )
    style.map("Small.TButton", background=[("active", SURFACE_ELEVATED)])

    style.configure(
        "Status.TLabel",
        background=SURFACE,
        foreground=TEXT_MUTED,
        relief=tk.FLAT,
        padding=(8, 4),
        font=("Segoe UI", 9),
    )

    style.configure("TPanedwindow", background=BG)
    style.configure("Sash", sashthickness=6, background=BORDER)

    return style
