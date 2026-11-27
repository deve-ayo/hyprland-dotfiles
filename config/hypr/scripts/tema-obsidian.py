#!/usr/bin/env python3
"""Gera snippet CSS 'wallust.css' em todos os cofres do Obsidian e o ativa em appearance.json."""
import colorsys
import json
from pathlib import Path

HOME = Path.home()
PALETA = HOME / ".cache/wallust/pywal.json"
OBSIDIAN_JSON = HOME / ".config/obsidian/obsidian.json"


def rgb(cor: str):
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def mistura(a: str, b: str, t: float) -> str:
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(x + (y - x) * t))) for x, y in zip(rgb(a), rgb(b))
    )


def hex_to_hsl(cor: str):
    r, g, b = (x / 255.0 for x in rgb(cor))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return round(h * 360), round(s * 100), round(l * 100)


def main():
    if not PALETA.exists() or not OBSIDIAN_JSON.exists():
        return

    paleta = json.loads(PALETA.read_text())
    colors = paleta.get("colors", {})
    bg = paleta["special"]["background"]
    fg = paleta["special"]["foreground"]
    accent = colors.get("color4", "#3b82f6")
    accent2 = colors.get("color6", accent)
    ah, asat, al = hex_to_hsl(accent)

    bg_alt = mistura(bg, fg, 0.04)
    bg_sec = mistura(bg, fg, 0.06)
    bg_sec_alt = mistura(bg, fg, 0.09)
    border = mistura(bg, fg, 0.16)
    muted = mistura(bg, fg, 0.58)
    faint = mistura(bg, fg, 0.35)
    accent_hover = mistura(accent, fg, 0.25)

    css = f"""/* Gerado automaticamente por tema-obsidian.py a partir do tema ativo — não edite. */
body.theme-dark, body.theme-light, :root {{
  --color-base-00: {bg} !important;
  --color-base-05: {mistura(bg, fg, 0.02)} !important;
  --color-base-10: {mistura(bg, fg, 0.04)} !important;
  --color-base-20: {mistura(bg, fg, 0.06)} !important;
  --color-base-25: {mistura(bg, fg, 0.09)} !important;
  --color-base-30: {mistura(bg, fg, 0.13)} !important;
  --color-base-35: {mistura(bg, fg, 0.17)} !important;
  --color-base-40: {mistura(bg, fg, 0.22)} !important;
  --color-base-50: {mistura(bg, fg, 0.38)} !important;
  --color-base-60: {mistura(bg, fg, 0.52)} !important;
  --color-base-70: {mistura(bg, fg, 0.68)} !important;
  --color-base-100: {fg} !important;

  --accent-h: {ah} !important;
  --accent-s: {asat}% !important;
  --accent-l: {al}% !important;
  --color-accent: {accent} !important;
  --color-accent-1: {accent} !important;
  --color-accent-2: {accent_hover} !important;

  --background-primary: {bg} !important;
  --background-primary-alt: {bg_alt} !important;
  --background-secondary: {bg_sec} !important;
  --background-secondary-alt: {bg_sec_alt} !important;
  --background-modifier-hover: {bg_sec_alt} !important;
  --background-modifier-border: {border} !important;
  --background-modifier-border-hover: {accent} !important;
  --background-modifier-border-focus: {accent} !important;
  --divider-color: {border} !important;
  --text-normal: {fg} !important;
  --text-muted: {muted} !important;
  --text-faint: {faint} !important;
  --text-accent: {accent} !important;
  --text-accent-hover: {accent_hover} !important;
  --interactive-normal: {bg_sec} !important;
  --interactive-hover: {bg_sec_alt} !important;
  --interactive-accent: {accent} !important;
  --interactive-accent-hover: {accent_hover} !important;
  --text-on-accent: {bg} !important;
  --code-background: {bg_alt} !important;
  --link-color: {accent} !important;
  --link-color-hover: {accent_hover} !important;
  --link-external-color: {accent2} !important;
  --tab-background-active: {bg} !important;
  --titlebar-background: {bg_sec} !important;
  --titlebar-background-focused: {bg_sec} !important;
  --ribbon-background: {bg_sec} !important;
  --ribbon-background-collapsed: {bg_sec} !important;
}}
"""

    obs_data = json.loads(OBSIDIAN_JSON.read_text())
    for vault in obs_data.get("vaults", {}).values():
        vpath = Path(vault.get("path", ""))
        obs_dir = vpath / ".obsidian"
        if not obs_dir.is_dir():
            continue

        snippets_dir = obs_dir / "snippets"
        snippets_dir.mkdir(parents=True, exist_ok=True)
        (snippets_dir / "wallust.css").write_text(css)

        app_file = obs_dir / "appearance.json"
        app = json.loads(app_file.read_text()) if app_file.exists() else {}
        enabled = app.get("enabledCssSnippets", [])
        if "wallust" not in enabled:
            enabled.append("wallust")
            app["enabledCssSnippets"] = enabled
            app_file.write_text(json.dumps(app, indent=2) + "\n")
        print(f"Tema Obsidian atualizado: {vpath}")


if __name__ == "__main__":
    main()
