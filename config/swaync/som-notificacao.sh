#!/bin/bash
# Som das notificações. O swaync chama este script a cada notificação recebida
# (config.json → "scripts" → "som") e passa os dados em variáveis SWAYNC_*.
#
# - um som por notificação nova; urgente toca o som de aviso; baixa prioridade fica muda
# - respeita o "não perturbe", a não ser que a notificação peça para furar
# - não toca quando a notificação só se atualiza (progresso, troca de música)
# - apps de música ficam mudos (o "plim" tocaria por cima da música)
# - várias notificações de uma vez tocam um som só (intervalo mínimo de 1 s)
# - se o app pedir um som próprio (hint sound-file / sound-name), usa o dele
TEMA=/usr/share/sounds/freedesktop/stereo
VOLUME=0.7
ULTIMO="${XDG_RUNTIME_DIR:-/tmp}/som-notificacao.ultimo"

urgencia="${SWAYNC_URGENCY,,}"
app="${SWAYNC_APP_NAME,,}"

[ "$urgencia" = low ] && exit 0
[ -n "${SWAYNC_REPLACES_ID:-}" ] && [ "$SWAYNC_REPLACES_ID" != 0 ] && exit 0
[ "$(printenv 'SWAYNC_HINT_suppress-sound')" = true ] && exit 0
case "$app" in
    *música*|*musica*|spotify|*player*) exit 0 ;;
esac
if [ -z "${SWAYNC_BYPASS_DND:-}" ] && [ "$(swaync-client -D 2>/dev/null)" = true ]; then
    exit 0
fi

agora=$(date +%s%N)
if [ -f "$ULTIMO" ] && [ $(( (agora - $(cat "$ULTIMO")) / 1000000 )) -lt 1000 ]; then
    exit 0
fi
echo "$agora" > "$ULTIMO"

som="$TEMA/message-new-instant.oga"
[ "$urgencia" = critical ] && som="$TEMA/dialog-warning.oga"
if [ -n "${SWAYNC_SOUND_FILE:-}" ] && [ -f "$SWAYNC_SOUND_FILE" ]; then
    som="$SWAYNC_SOUND_FILE"
elif [ -n "${SWAYNC_SOUND_NAME:-}" ] && [ -f "$TEMA/$SWAYNC_SOUND_NAME.oga" ]; then
    som="$TEMA/$SWAYNC_SOUND_NAME.oga"
fi

exec pw-play --volume "$VOLUME" "$som"
