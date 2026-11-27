#!/usr/bin/env bash
# Ajusta o volume da saída de áudio que está em uso no momento.
# Se houver aplicativo reproduzindo som, altera o volume dessa saída.
# Caso contrário, altera o volume da saída padrão.

alvo() {
    local padrao
    padrao=$(pactl get-default-sink 2>/dev/null)
    local sink
    sink=$(pactl -f json list sinks 2>/dev/null | jq -r --arg padrao "$padrao" \
        --argjson inputs "$(pactl -f json list sink-inputs 2>/dev/null || echo '[]')" '
        [ .[] | . as $s | {name, index, state,
            ativos: ([ $inputs[] | select(.sink == $s.index and (.corked | not)) ] | length)} ] as $sinks
        | ($sinks | map(select(.name == $padrao and .ativos > 0)) | first)
          // ($sinks | map(select(.ativos > 0)) | sort_by(.ativos, .index) | last)
          // ($sinks | map(select(.state == "RUNNING")) | first)
          // {name: $padrao}
        | .name' 2>/dev/null)
    echo "${sink:-$padrao}"
}

acao="${1:-lower}"
sink=$(alvo)

padrao=$(pactl get-default-sink 2>/dev/null)
if [ -n "$sink" ] && [ "$sink" != "$padrao" ]; then
    pactl set-default-sink "$sink" 2>/dev/null
fi

cmd=(swayosd-client)
[ -n "$sink" ] && cmd+=(--device "$sink")

case "$acao" in
    raise)
        "${cmd[@]}" --output-volume raise --max-volume 100
        ;;
    lower)
        "${cmd[@]}" --output-volume lower
        ;;
    mute-toggle|mute)
        "${cmd[@]}" --output-volume mute-toggle
        ;;
    *)
        "${cmd[@]}" --output-volume "$acao" "${@:2}"
        ;;
esac
