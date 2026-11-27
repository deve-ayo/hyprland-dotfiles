#!/usr/bin/env python3
"""Gera o tema de ícones ~/.local/share/icons/Wallust-Folders com as cores das pastas
acompanhando a paleta ativa do wallust (~/.cache/wallust/pywal.json) para o Nautilus e apps GTK.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
PALETA = HOME / ".cache/wallust/pywal.json"
SRC_PLACES = Path("/usr/share/icons/Tela-circle-black-dark/scalable/places")
DEST_THEME = HOME / ".local/share/icons/Wallust-Folders"
DEST_PLACES = DEST_THEME / "scalable/places"


def rgb(cor: str):
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def mistura(a: str, b: str, t: float) -> str:
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(x + (y - x) * t))) for x, y in zip(rgb(a), rgb(b))
    )


def main():
    if not PALETA.exists() or not SRC_PLACES.is_dir():
        return

    paleta = json.loads(PALETA.read_text())
    bg = paleta["special"]["background"]
    fg = paleta["special"]["foreground"]
    accent = paleta.get("colors", {}).get("color4", "#3b82f6")

    folder_color = mistura(accent, fg, 0.20)
    glyph_color = mistura(bg, "#000000", 0.35)
    paper_color = mistura(fg, "#ffffff", 0.30)

    DEST_PLACES.mkdir(parents=True, exist_ok=True)

    index_content = """[Icon Theme]
Name=Wallust Folders
Comment=Dynamic folder colors from wallust, inheriting Tela-circle-black-dark
Inherits=Tela-circle-black-dark,Tela-circle-black,breeze-dark,Adwaita,hicolor
Example=folder

Directories=scalable/places

[scalable/places]
Size=64
MinSize=16
MaxSize=512
Type=Scalable
Context=Places
"""
    (DEST_THEME / "index.theme").write_text(index_content)

    for entry in SRC_PLACES.iterdir():
        name = entry.name
        if not (name.startswith("default-folder") or name.startswith("folder")):
            continue
        dest = DEST_PLACES / name
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        if entry.is_symlink():
            os.symlink(os.readlink(entry), dest)
        elif entry.is_file() and name.endswith(".svg"):
            svg = entry.read_text()
            svg = re.sub(r"#4d4d4d\b", folder_color, svg, flags=re.IGNORECASE)
            svg = re.sub(r"#333333\b", glyph_color, svg, flags=re.IGNORECASE)
            svg = re.sub(r"#ffffff\b", paper_color, svg, flags=re.IGNORECASE)
            dest.write_text(svg)

    if shutil.which("gtk-update-icon-cache"):
        subprocess.run(
            ["gtk-update-icon-cache", "-f", "-t", str(DEST_THEME)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Alterna rapidamente para forçar o Nautilus / GTK4 a recarregar o cache de ícones ao vivo
    subprocess.run(
        ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Tela-circle-black-dark"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Wallust-Folders"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    gtk3_ini = HOME / ".config/gtk-3.0/settings.ini"
    if gtk3_ini.exists():
        text = gtk3_ini.read_text()
        text = re.sub(r"(?m)^gtk-icon-theme-name=.*$", "gtk-icon-theme-name=Wallust-Folders", text)
        gtk3_ini.write_text(text)


if __name__ == "__main__":
    main()
