#!/usr/bin/env python3
"""Leva as cores do papel de parede (wallust) para os apps Qt/KDE (Dolphin, Okular, Ark,
Gwenview, VLC...). Chamado pelo wallpaper.sh depois do wallust, com o modo (claro|escuro).

- Kvantum: gera o tema ~/.config/Kvantum/Wallust a partir do Orchis-BW (mesmo desenho),
  trocando cada cinza por uma mistura do fundo com o texto do papel de parede.
- KDE: gera o esquema de cores "Wallust" e aplica no kdeglobals (os apps KDE leem dele
  algumas cores próprias, como seleção e links).
- qt6ct: troca o tema de ícones conforme o modo.

Os apps Qt só leem o tema ao abrir: vale para os apps abertos depois da troca.
"""
import configparser
import json
import re
import sys
from pathlib import Path

HOME = Path.home()
PALETA = HOME / ".cache/wallust/pywal.json"
ORIGEM = HOME / ".config/Kvantum/Orchis-BW"           # tema base (o desenho); não é alterado
DESTINO = HOME / ".config/Kvantum/Wallust"

# No Orchis-BW a janela é #212121 e o texto #dfdfdf: cada cinza vira o ponto equivalente
# entre o fundo e o texto do papel de parede (mais escuro que a janela = além do fundo).
CINZA_FUNDO, CINZA_TEXTO = 0x21, 0xDF

ICONES = {"claro": "Tela-circle-black", "escuro": "Tela-circle-black-dark"}


def rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def mistura(a, b, t):
    """Mistura a→b; t fora de 0..1 extrapola (limitado a 0..255)."""
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x + (y - x) * t)))
                                   for x, y in zip(rgb(a), rgb(b)))


modo = sys.argv[1] if len(sys.argv) > 1 else "escuro"
paleta = json.loads(PALETA.read_text())
fundo = paleta["special"]["background"]
texto = paleta["special"]["foreground"]
cor_destaque = paleta.get("colors", {}).get("color4", "#3b82f6")
destaque = mistura(texto, cor_destaque, 0.55)


def recolorir(cor):
    cor = {"white": "#ffffff", "black": "#000000"}.get(cor.lower(), cor)
    if len(cor) == 4:                                   # #abc
        cor = "#" + "".join(c * 2 for c in cor[1:])
    if cor.lower() == "#000000":                        # sombras continuam pretas
        return cor
    r, g, b = rgb(cor)
    cinza = 0.299 * r + 0.587 * g + 0.114 * b
    return mistura(fundo, texto, (cinza - CINZA_FUNDO) / (CINZA_TEXTO - CINZA_FUNDO))


HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")

# ---- Kvantum ----
SVG_ORIGEM = ORIGEM / "Orchis-BW.svg"
KV_ORIGEM = ORIGEM / "Orchis-BW.kvconfig"
if not SVG_ORIGEM.is_file() or not KV_ORIGEM.is_file():
    # O tema AUR atual instala Orchis com estes nomes globais, sem o sufixo BW.
    ORIGEM = Path("/usr/share/Kvantum/Orchis")
    SVG_ORIGEM = ORIGEM / "Orchis.svg"
    KV_ORIGEM = ORIGEM / "Orchis.kvconfig"
if not SVG_ORIGEM.is_file() or not KV_ORIGEM.is_file():
    sys.exit(0)

DESTINO.mkdir(parents=True, exist_ok=True)
svg = HEX.sub(lambda m: recolorir(m.group()), SVG_ORIGEM.read_text())
(DESTINO / "Wallust.svg").write_text(svg)

linhas = []
for linha in KV_ORIGEM.read_text().splitlines():
    chave, igual, valor = linha.partition("=")
    chave = chave.strip()
    if igual and chave.endswith("color"):
        if chave == "highlight.color":
            valor = destaque
        elif chave == "inactive.highlight.color":
            valor = mistura(fundo, destaque, 0.5)
        elif chave == "highlight.text.color":
            valor = fundo
        elif chave in ("link.color", "link.visited.color"):
            valor = destaque if chave == "link.color" else mistura(destaque, texto, 0.4)
        else:
            valor = re.sub(r"#[0-9a-fA-F]{3,6}\b|\b(?:white|black)\b",
                           lambda m: recolorir(m.group()), valor.strip())
        linha = f"{chave}={valor}"
    linhas.append(linha)
(DESTINO / "Wallust.kvconfig").write_text(
    "# Gerado pelo ~/.config/hypr/scripts/tema-qt.py a partir do Orchis-BW — não edite.\n"
    + "\n".join(linhas) + "\n")

kv = HOME / ".config/Kvantum/kvantum.kvconfig"
kv.write_text("[General]\ntheme=Wallust\n")

# ---- Esquema de cores KDE ----
def kde(cor):
    return ",".join(map(str, rgb(cor)))


fraco = mistura(fundo, texto, 0.55)
vermelho, amarelo, verde = (mistura(texto, c, 0.6) for c in ("#e5484d", "#d4a017", "#30a46c"))
comum = {
    "ForegroundInactive": kde(fraco), "ForegroundActive": kde(destaque),
    "ForegroundLink": kde(destaque), "ForegroundVisited": kde(mistura(destaque, texto, 0.4)),
    "ForegroundNegative": kde(vermelho), "ForegroundNeutral": kde(amarelo),
    "ForegroundPositive": kde(verde),
    "DecorationFocus": kde(destaque), "DecorationHover": kde(mistura(fundo, destaque, 0.6)),
}
grupos = {
    "Window": (fundo, mistura(fundo, texto, 0.04), texto),
    "View": (mistura(fundo, texto, 0.03), mistura(fundo, texto, 0.07), texto),
    "Button": (mistura(fundo, texto, 0.10), mistura(fundo, texto, 0.14), texto),
    "Header": (mistura(fundo, texto, 0.06), mistura(fundo, texto, 0.08), texto),
    "Tooltip": (mistura(fundo, texto, 0.08), mistura(fundo, texto, 0.10), texto),
    "Complementary": (texto, mistura(texto, fundo, 0.08), fundo),
    "Selection": (destaque, mistura(destaque, fundo, 0.2), fundo),
}
esquema = configparser.ConfigParser(interpolation=None)
esquema.optionxform = str
esquema["General"] = {"Name": "Wallust", "ColorScheme": "Wallust"}
for nome, (bg, bg_alt, fg) in grupos.items():
    esquema[f"Colors:{nome}"] = {"BackgroundNormal": kde(bg), "BackgroundAlternate": kde(bg_alt),
                                 "ForegroundNormal": kde(fg), **comum}
esquema["Colors:Selection"]["ForegroundInactive"] = kde(mistura(fundo, destaque, 0.3))
esquema["WM"] = {"activeBackground": kde(grupos["Header"][0]), "activeForeground": kde(texto),
                 "inactiveBackground": kde(fundo), "inactiveForeground": kde(fraco)}

pasta = HOME / ".local/share/color-schemes"
pasta.mkdir(parents=True, exist_ok=True)
with open(pasta / "Wallust.colors", "w") as f:
    esquema.write(f, space_around_delimiters=False)

# kdeglobals: mesmas seções + esquema ativo (o resto do arquivo é preservado)
glob = configparser.ConfigParser(interpolation=None, strict=False)
glob.optionxform = str
arq = HOME / ".config/kdeglobals"
glob.read(arq)
for secao in esquema.sections():
    if secao.startswith("Colors:") or secao == "WM":
        glob[secao] = dict(esquema[secao])
if not glob.has_section("General"):
    glob.add_section("General")
glob["General"]["ColorScheme"] = "Wallust"
if not glob.has_section("Icons"):
    glob.add_section("Icons")
glob["Icons"]["Theme"] = ICONES[modo]
with open(arq, "w") as f:
    glob.write(f, space_around_delimiters=False)

# ---- qt6ct: ícones conforme o modo ----
qt6ct = HOME / ".config/qt6ct/qt6ct.conf"
qt6ct.parent.mkdir(parents=True, exist_ok=True)
conteudo = qt6ct.read_text() if qt6ct.exists() else "[Appearance]\n"
if re.search(r"(?m)^icon_theme=.*$", conteudo):
    conteudo = re.sub(r"(?m)^icon_theme=.*$", f"icon_theme={ICONES[modo]}", conteudo)
elif "[Appearance]" in conteudo:
    conteudo = conteudo.replace("[Appearance]", f"[Appearance]\nicon_theme={ICONES[modo]}", 1)
else:
    conteudo += f"\n[Appearance]\nicon_theme={ICONES[modo]}\n"
qt6ct.write_text(conteudo)
