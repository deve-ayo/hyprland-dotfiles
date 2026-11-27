#!/bin/bash
# Handler para o switch da tampa do notebook (chamado pelo hyprland.lua).
#
# Fechar a tampa:
#   - com monitor externo conectado -> apenas desliga o painel interno (eDP-1),
#     o sistema continua funcionando normalmente no monitor externo.
#   - sem monitor externo, NA TOMADA -> bloqueia com hyprlock e apaga a tela, mas NÃO suspende:
#     os servidores desta máquina (Nossos Dias e Ayo Std) continuam no ar.
#     Se a tomada sair com a tampa ainda fechada, suspende em até 30 s (protege a bateria).
#     Enquanto isso fica no perfil de energia "power-saver"; ao abrir, volta o perfil anterior.
#   - sem monitor externo, NA BATERIA -> bloqueia com hyprlock e suspende (economia de energia).
#
# Abrir a tampa:
#   - religa a tela e o painel interno com resolução/escala originais.
#
# Versão anterior (sempre suspendia sem monitor externo): lid.sh.bak-2026-10-01

INTERNAL="eDP-1"
ACTION="$1"
AC_ONLINE="/sys/class/power_supply/AC/online"
VIGIA_PID="${XDG_RUNTIME_DIR:-/tmp}/lid-vigia.pid"
PERFIL_SALVO="${XDG_RUNTIME_DIR:-/tmp}/lid-perfil-energia"

na_tomada() { [ "$(cat "$AC_ONLINE" 2>/dev/null)" = "1" ]; }
tampa_fechada() { grep -q closed /proc/acpi/button/lid/*/state 2>/dev/null; }

# Liga o DPMS de cada monitor ativo, um por um (o dpms("on") global não bastava).
ligar_telas() {
    for m in $(hyprctl monitors -j | jq -r '.[].name'); do
        hyprctl dispatch "hl.dsp.dpms({ action = 'on', monitor = '$m' })" >/dev/null
    done
}

economia_on() {
    [ -f "$PERFIL_SALVO" ] || powerprofilesctl get > "$PERFIL_SALVO" 2>/dev/null
    powerprofilesctl set power-saver 2>/dev/null
}

economia_off() {
    if [ -f "$PERFIL_SALVO" ]; then
        powerprofilesctl set "$(cat "$PERFIL_SALVO")" 2>/dev/null
        rm -f "$PERFIL_SALVO"
    fi
}

parar_vigia() {
    if [ -f "$VIGIA_PID" ]; then
        kill "$(cat "$VIGIA_PID")" 2>/dev/null
        rm -f "$VIGIA_PID"
    fi
}

case "$ACTION" in
    close)
        external_count=$(hyprctl monitors -j | jq --arg internal "$INTERNAL" '[.[] | select(.name != $internal)] | length')

        if [ "$external_count" -gt 0 ]; then
            hyprctl eval "hl.monitor({ output = '$INTERNAL', disabled = true })"
            sleep 1
            ligar_telas
        elif na_tomada; then
            loginctl lock-session
            sleep 1
            hyprctl dispatch 'hl.dsp.dpms("off")'
            economia_on
            parar_vigia
            (
                while tampa_fechada; do
                    if ! na_tomada; then
                        systemctl suspend
                        break
                    fi
                    sleep 30
                done
                rm -f "$VIGIA_PID"
            ) &
            echo $! > "$VIGIA_PID"
        else
            loginctl lock-session
            sleep 1
            systemctl suspend
        fi
        ;;
    open)
        parar_vigia
        economia_off
        # mesmos valores do hl.monitor de eDP-1 no hyprland.lua (antes: 1920x0 escala 1.25,
        # que sobrepunha o painel ao monitor HDMI)
        hyprctl eval "hl.monitor({ output = '$INTERNAL', disabled = false, mode = '1920x1080@60', position = '0x0', scale = 1 })"
        # Só DEPOIS de religar o painel: o modeset do eDP-1 deixava o HDMI em DPMS off
        # (tela externa apagada com a tampa aberta). Antes o dpms("on") vinha primeiro.
        sleep 1
        ligar_telas
        ;;
esac
