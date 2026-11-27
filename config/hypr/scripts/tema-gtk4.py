#!/usr/bin/env python3
"""Gera ~/.config/gtk-4.0/gtk.css (e o gtk-3.0) com as cores do papel de parede (wallust) para os
apps GTK4/libadwaita, como os apps Ayo. Chamado pelo wallpaper.sh depois do wallust.

O claro/escuro dos apps muda na hora (gsettings color-scheme, no wallpaper.sh); as
cores deste arquivo valem para os apps abertos a partir da troca.
"""
import json
from pathlib import Path

PALETA = Path.home() / ".cache/wallust/pywal.json"
DESTINO = Path.home() / ".config/gtk-4.0/gtk.css"
DESTINO_GTK3 = Path.home() / ".config/gtk-3.0/gtk.css"


def rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def mistura(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(rgb(a), rgb(b)))


paleta = json.loads(PALETA.read_text())
fundo = paleta["special"]["background"]
texto = paleta["special"]["foreground"]
cor_destaque = paleta.get("colors", {}).get("color4", "#82c4f8")
destaque = mistura(texto, cor_destaque, 0.85)

cores = {
    "window-bg-color": fundo,                       "window-fg-color": texto,
    "view-bg-color": mistura(fundo, texto, 0.04),   "view-fg-color": texto,
    "headerbar-bg-color": mistura(fundo, texto, 0.07), "headerbar-fg-color": texto,
    "headerbar-backdrop-color": fundo,
    "sidebar-bg-color": mistura(fundo, texto, 0.05), "sidebar-fg-color": texto,
    "sidebar-backdrop-color": mistura(fundo, texto, 0.03),
    "secondary-sidebar-bg-color": mistura(fundo, texto, 0.04), "secondary-sidebar-fg-color": texto,
    "card-bg-color": mistura(fundo, texto, 0.07),   "card-fg-color": texto,
    "dialog-bg-color": mistura(fundo, texto, 0.06), "dialog-fg-color": texto,
    "popover-bg-color": mistura(fundo, texto, 0.08), "popover-fg-color": texto,
    "thumbnail-bg-color": mistura(fundo, texto, 0.07), "thumbnail-fg-color": texto,
    "accent-bg-color": destaque, "accent-fg-color": fundo, "accent-color": destaque,
}

linhas = ["/* Gerado pelo ~/.config/hypr/scripts/tema-gtk4.py a partir do wallust — não edite. */",
          "/* Cores do papel de parede para apps GTK4/libadwaita (apps Ayo). */", "", ":root {"]
linhas += [f"    --{nome}: {valor};" for nome, valor in cores.items()]
linhas += ["}", "", "/* Nomes antigos (@define-color), para apps e temas que ainda usam */"]
linhas += [f"@define-color {nome.replace('-', '_')} {valor};" for nome, valor in cores.items()]

DESTINO.parent.mkdir(parents=True, exist_ok=True)
DESTINO.write_text("\n".join(linhas) + "\n")

# GTK3 (tema adw-gtk3, que usa os mesmos nomes de cor da libadwaita; Firefox e Brave no
# modo "tema do sistema" também seguem) — só aceita @define-color
gtk3 = ["/* Gerado pelo ~/.config/hypr/scripts/tema-gtk4.py a partir do wallust — não edite. */",
        "/* Cores do papel de parede para apps GTK3 com o tema adw-gtk3. */", ""]
gtk3 += [f"@define-color {nome.replace('-', '_')} {valor};" for nome, valor in cores.items()]
DESTINO_GTK3.parent.mkdir(parents=True, exist_ok=True)
DESTINO_GTK3.write_text("\n".join(gtk3) + "\n")
