#!/usr/bin/env python3
"""Gera o tema Wallust para o Spicetify (~/.config/spicetify/Themes/Wallust/color.ini)
a partir de ~/.cache/wallust/pywal.json e aplica se /opt/spotify estiver liberado.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
PALETA = HOME / ".cache/wallust/pywal.json"
THEME_DIR = HOME / ".config/spicetify/Themes/Wallust"
SPOTIFY_APPS = Path("/opt/spotify/Apps")


def rgb(cor: str):
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def mistura(a: str, b: str, t: float) -> str:
    return "%02x%02x%02x" % tuple(
        max(0, min(255, round(x + (y - x) * t))) for x, y in zip(rgb(a), rgb(b))
    )


def bare(cor: str) -> str:
    return cor.lstrip("#").lower()


def main():
    if not PALETA.exists() or not shutil.which("spicetify"):
        return

    paleta = json.loads(PALETA.read_text())
    colors = paleta.get("colors", {})
    bg = paleta["special"]["background"]
    fg = paleta["special"]["foreground"]
    accent = colors.get("color4", "#3b82f6")
    err = colors.get("color1", "#e5484d")

    color_ini = f"""# Gerado automaticamente por tema-spotify.py — não edite.
[Wallust]
text               = {bare(fg)}
subtext            = {mistura(bg, fg, 0.65)}
main               = {bare(bg)}
main-elevated      = {mistura(bg, fg, 0.06)}
highlight          = {mistura(bg, fg, 0.10)}
highlight-elevated = {mistura(bg, fg, 0.14)}
sidebar            = {mistura(bg, '#000000', 0.18)}
player             = {mistura(bg, fg, 0.03)}
card               = {mistura(bg, fg, 0.05)}
shadow             = 000000
selected-row       = {mistura(bg, fg, 0.85)}
button             = {bare(accent)}
button-active      = {mistura(accent, fg, 0.20)}
button-disabled    = {mistura(bg, fg, 0.25)}
tab-active         = {mistura(bg, fg, 0.08)}
notification       = {bare(accent)}
notification-error = {bare(err)}
misc               = {mistura(bg, fg, 0.45)}
"""

    THEME_DIR.mkdir(parents=True, exist_ok=True)
    (THEME_DIR / "color.ini").write_text(color_ini)
    user_css = THEME_DIR / "user.css"
    user_css.write_text("""/* Tema Wallust para Spicetify */
:root, .encore-dark-theme, .encore-base-set {
  --background-base: var(--spice-main) !important;
  --background-highlight: var(--spice-highlight) !important;
  --background-press: var(--spice-highlight-elevated) !important;
  --background-elevated-base: var(--spice-main-elevated) !important;
  --background-elevated-highlight: var(--spice-highlight-elevated) !important;
  --background-tinted-base: rgba(var(--spice-rgb-selected-row), 0.08) !important;
  --background-tinted-highlight: rgba(var(--spice-rgb-selected-row), 0.14) !important;
  --text-base: var(--spice-text) !important;
  --text-subdued: var(--spice-subtext) !important;
  --text-bright-accent: var(--spice-button) !important;
  --essential-bright-accent: var(--spice-button) !important;
  --essential-base: var(--spice-text) !important;
}
""")

    if SPOTIFY_APPS.exists() and os.access(SPOTIFY_APPS, os.W_OK):
        subprocess.run(
            ["spicetify", "config", "current_theme", "Wallust", "color_scheme", "Wallust"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        spotify_running = subprocess.run(
            ["pgrep", "-x", "spotify"], stdout=subprocess.DEVNULL
        ).returncode == 0
        cmd = ["spicetify", "apply"] if spotify_running else ["spicetify", "apply", "-n"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Tema Spicetify atualizado: Wallust")
    else:
        print("Spicetify color.ini gerado; aguardando permissão em /opt/spotify para aplicar.")


if __name__ == "__main__":
    main()
