#!/usr/bin/env python3
"""Alterna entre telas estendidas, espelhadas, externa apenas e interna apenas."""
import json
import subprocess
import sys
import time

INTERNA = "eDP-1"
EXTERNA = "HDMI-A-2"


def hypr(*args):
    return subprocess.check_output(["hyprctl", *args], text=True).strip()


def regra(output, modo="1920x1080@60", posicao="0x0", espelho=None, desativada=False):
    campos = [f'output = "{output}"']
    if desativada:
        campos.append("disabled = true")
    else:
        campos.extend((f'mode = "{modo}"', f'position = "{posicao}"', "scale = 1", "disabled = false"))
        if espelho:
            campos.append(f'mirror = "{espelho}"')
        else:
            # Regras do monitor persistem no Hyprland; sem limpar o campo,
            # uma regra anterior de espelhamento continua ativa.
            campos.append('mirror = ""')
    hypr("eval", "hl.monitor({ " + ", ".join(campos) + " })")


def avisar(texto):
    subprocess.run(["notify-send", "Modo de telas", texto], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


try:
    monitores = json.loads(hypr("monitors", "all", "-j"))
except (subprocess.CalledProcessError, json.JSONDecodeError) as erro:
    print(f"Não consegui consultar os monitores: {erro}", file=sys.stderr)
    sys.exit(1)

por_nome = {m.get("name"): m for m in monitores}
ativos = {nome for nome, m in por_nome.items() if not m.get("disabled", False)}
if INTERNA not in por_nome or EXTERNA not in por_nome:
    avisar("O ciclo de modos requer a tela interna e o monitor HDMI conectados.")
    sys.exit(1)

if {INTERNA, EXTERNA}.issubset(ativos):
    atual = "espelhado" if any(por_nome[n].get("mirrorOf", "none") != "none" for n in (INTERNA, EXTERNA)) else "estendido"
elif INTERNA in ativos:
    atual = "interna"
elif EXTERNA in ativos:
    atual = "externa"
else:
    avisar("Não há uma tela ativa para alternar.")
    sys.exit(1)

proximo = {"estendido": "espelhado", "espelhado": "externa", "externa": "interna", "interna": "estendido"}[atual]

if proximo == "espelhado":
    # Usa o painel interno a 60 Hz como origem para manter os dois monitores em 1080p.
    regra(INTERNA)
    regra(EXTERNA, modo="1920x1080@60", espelho=INTERNA)
elif proximo == "estendido":
    # Coloca primeiro o externo fora da área do painel interno; assim não há
    # sobreposição transitória ao sair dos modos interno/externo apenas.
    regra(EXTERNA, modo="1920x1080@120", posicao="1920x0")
    regra(INTERNA)
elif proximo == "externa":
    # Libera o HDMI em uma posição separada antes de desligar o painel interno.
    regra(EXTERNA, modo="1920x1080@120", posicao="1920x0")
    regra(INTERNA, desativada=True)
    regra(EXTERNA, modo="1920x1080@120")
else:
    regra(EXTERNA, desativada=True)
    regra(INTERNA)

# Waybar pode manter a instância associada à tela que acabou de ser desligada.
# Reiniciá-la após o modeset faz a barra ser criada no monitor que ficou ativo.
time.sleep(0.5)
subprocess.run(["systemctl", "--user", "restart", "waybar.service"], check=False)
subprocess.run(["systemctl", "--user", "try-restart", "cava-fundo.service"], check=False)

nomes = {"estendido": "Telas estendidas", "espelhado": "Telas espelhadas",
         "externa": "Somente monitor externo", "interna": "Somente tela interna"}
avisar(nomes[proximo])
