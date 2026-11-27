#!/bin/bash
# Luz noturna (hyprsunset). Uso: luz-noturna.sh [alternar|mais|menos]
#   alternar  liga/desliga na hora (só tocar SUPER+N)
#   mais      mais forte: cor mais quente  (segurando SUPER depois do N, seta →)
#   menos     mais fraca: cor mais neutra  (segurando SUPER depois do N, seta ←)
# A intensidade escolhida fica salva no perfil das 19:00 do hyprsunset.conf, então vale
# também nos próximos dias. O horário automático continua: na próxima troca (19:00 liga,
# 06:30 desliga) ele volta a mandar e o liga/desliga manual é esquecido.
# O hyprsunset não informa se o filtro está ligado (a temperatura consultada é sempre a
# configurada), por isso o último toque fica guardado em $ESTADO.
CONF="$HOME/.config/hypr/hyprsunset.conf"
ESTADO="${XDG_RUNTIME_DIR:-/tmp}/luz-noturna"   # "<ligada|desligada> <epoch do toque>"
PASSO=250
MAIS_QUENTE=2500     # intensidade máxima
MAIS_NEUTRA=6000     # intensidade mínima

temperatura() {      # a do perfil das 19:00
    local t
    t=$(awk '/time = 19:00/ { achou = 1 } achou && /temperature/ { print $3; exit }' "$CONF")
    echo "${t:-4500}"
}

salvar_temperatura() {
    sed -i "/time = 19:00/,/}/ s/temperature = [0-9]*/temperature = $1/" "$CONF"
}

pelo_horario() {
    local agora=$((10#$(date +%H%M)))
    if [ "$agora" -ge 1900 ] || [ "$agora" -lt 630 ]; then echo ligada; else echo desligada; fi
}

ultima_troca() {     # epoch da troca de horário mais recente (06:30 ou 19:00)
    local agora t b
    agora=$(date +%s)
    for b in "today 19:00" "today 06:30" "yesterday 19:00"; do
        t=$(date -d "$b" +%s)
        if [ "$t" -le "$agora" ]; then echo "$t"; return; fi
    done
}

estado_atual() {
    local atual manual quando
    atual=$(pelo_horario)
    if [ -f "$ESTADO" ]; then
        read -r manual quando < "$ESTADO"
        if [ -n "$quando" ] && [ "$quando" -gt "$(ultima_troca)" ]; then
            atual=$manual
        fi
    fi
    echo "$atual"
}

ligar() {
    hyprctl hyprsunset identity false >/dev/null
    hyprctl hyprsunset temperature "$1" >/dev/null
    echo "ligada $(date +%s)" > "$ESTADO"
}

avisar() {           # mensagem e, opcionalmente, a barra de intensidade
    local t=$2
    if [ -n "$t" ]; then
        local nivel
        nivel=$(awk -v t="$t" -v q="$MAIS_QUENTE" -v n="$MAIS_NEUTRA" 'BEGIN { printf "%.2f", (n - t) / (n - q) }')
        swayosd-client --custom-progress "$nivel" --custom-progress-text "$1 · ${t} K" \
            --custom-icon night-light-symbolic 2>/dev/null && return
    else
        swayosd-client --custom-message "$1" --custom-icon night-light-symbolic 2>/dev/null && return
    fi
    notify-send -t 1500 "Luz noturna" "$1${t:+ ($t K)}"
}

t=$(temperatura)
case "${1:-alternar}" in
    mais|menos)
        if [ "$1" = mais ]; then t=$((t - PASSO)); else t=$((t + PASSO)); fi
        [ "$t" -lt "$MAIS_QUENTE" ] && t=$MAIS_QUENTE
        [ "$t" -gt "$MAIS_NEUTRA" ] && t=$MAIS_NEUTRA
        salvar_temperatura "$t"
        ligar "$t"
        avisar "Luz noturna" "$t"
        ;;
    alternar)
        if [ "$(estado_atual)" = ligada ]; then
            hyprctl hyprsunset identity true >/dev/null
            echo "desligada $(date +%s)" > "$ESTADO"
            avisar "Luz noturna desligada"
        else
            ligar "$t"
            avisar "Luz noturna ligada" "$t"
        fi
        ;;
    *)
        echo "Uso: $(basename "$0") [alternar|mais|menos]" >&2
        exit 1
        ;;
esac
