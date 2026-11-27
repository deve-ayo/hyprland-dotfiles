#!/usr/bin/env python3
"""Diz ao wallpaper.sh se o papel de parede é claro ou escuro e se tem fundo liso.

Uso: analisar-papel.py <imagem>   (a saída é lida com eval no bash)
  MODO=claro|escuro
  FUNDO=#RRGGBB    vazio quando o fundo não é de uma cor só

Fundo liso = a maior parte da borda da imagem tem a mesma cor (desenho ou mangá em
fundo de uma cor). Nesse caso o wallpaper.sh usa essa cor como fundo do tema, e
terminal, barra e apps ficam com o mesmo fundo do papel de parede.
"""
import subprocess
import sys
from collections import Counter

LIMITE_CLARO = 0.55     # luminância média a partir da qual o tema fica claro
FRACAO_LISA = 0.6       # fração da borda com a mesma cor para considerar o fundo liso


def luminancia(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255


imagem = f"{sys.argv[1]}[0]"  # GIFs usam o primeiro quadro
processo = subprocess.run(
    ["magick", imagem, "-thumbnail", "320x320", "-background", "black",
     "-alpha", "remove", "-alpha", "off", "-colorspace", "sRGB", "-depth", "8", "rgb:-"],
    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
dimensoes = subprocess.run(
    ["magick", imagem, "-thumbnail", "320x320", "-format", "%w %h", "info:"],
    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
).stdout
w, h = map(int, dimensoes.split())
dados = processo.stdout
if len(dados) != w * h * 3:
    raise RuntimeError(f"Leitura incompleta da imagem: {sys.argv[1]}")

def pixel(x, y):
    i = (y * w + x) * 3
    return tuple(dados[i:i + 3])

borda = [pixel(x, y) for x in range(w) for y in (0, 1, h - 2, h - 1)]
borda += [pixel(x, y) for y in range(h) for x in (0, 1, w - 2, w - 1)]
grupos = Counter((r // 8, g // 8, b // 8) for r, g, b in borda)
chave, quantos = grupos.most_common(1)[0]

fundo = None
if quantos / len(borda) >= FRACAO_LISA:
    iguais = [c for c in borda if (c[0] // 8, c[1] // 8, c[2] // 8) == chave]
    fundo = tuple(round(sum(v) / len(iguais)) for v in zip(*iguais))

if fundo:
    claro = luminancia(fundo) >= LIMITE_CLARO
else:
    claro = sum(luminancia(pixel(x, y)) for y in range(h) for x in range(w)) / (w * h) >= LIMITE_CLARO

print(f"MODO={'claro' if claro else 'escuro'}")
print("FUNDO=" + ("#%02X%02X%02X" % fundo if fundo else ""))
