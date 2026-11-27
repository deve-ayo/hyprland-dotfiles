#!/bin/bash
# Troca o papel de parede (awww) e regenera as cores do rice (wallust).
#
# Uso:
#   wallpaper.sh <imagem>   usa essa imagem
#   wallpaper.sh --pick     escolhe no wofi (com miniaturas)
#   wallpaper.sh --random   sorteia uma imagem de $WALL_DIR
#   wallpaper.sh --reload   só recarrega as cores nos programas abertos

WALL_DIR="${WALL_DIR:-$HOME/Pictures/wallpapers}"
THEMES_INDEX="$HOME/.config/hypr/themes/themes.tsv"
CACHE="$HOME/.cache/wallust"
CURRENT="$CACHE/current_wallpaper"
CURRENT_THEME="$CACHE/current_theme"

# Transição do awww: simple, fade, left, right, top, bottom, wipe, wave, grow, center, any, outer, random
TRANSITION="${TRANSITION:-grow}"
TRANSITION_DURATION="${TRANSITION_DURATION:-1.2}"

list_images() {
    find -L "$WALL_DIR" -maxdepth 1 -type f \
        \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) | sort
}

list_themes() {
    [ -f "$THEMES_INDEX" ] || return 0
    while IFS=$'\t' read -r slug name kitty wall json; do
        [ -n "$slug" ] && [ -f "$wall" ] && printf '%s\t%s\t%s\n' "$slug" "$name" "$wall"
    done < "$THEMES_INDEX"
}

theme_slug_for_image() {
    [ -f "$THEMES_INDEX" ] || return 0
    local target
    target="$(readlink -f "$1" 2>/dev/null || printf '%s' "$1")"
    while IFS=$'\t' read -r slug name kitty wall json; do
        [ -z "$wall" ] && continue
        if [ "$(readlink -f "$wall" 2>/dev/null || printf '%s' "$wall")" = "$target" ]; then
            printf '%s\n' "$slug"
            return 0
        fi
    done < "$THEMES_INDEX"
}

pick() {
    {
        list_themes | while IFS=$'\t' read -r slug name wall; do
            printf 'img:%s:text:[Rice] %s\n' "$wall" "$name"
        done
        list_images | while read -r f; do
            printf 'img:%s:text:%s\n' "$f" "$(basename "$f")"
        done
    } | wofi --dmenu --allow-images --cache-file /dev/null --prompt "Papel de parede / Rice" \
      | sed -E 's/^img:(.*):text:.*$/\1/'
}

random_image() {
    local current
    current="$(readlink -f "$CURRENT" 2>/dev/null)"
    {
        list_themes | cut -f3
        list_images
    } | grep -vxF "$current" | shuf -n1
}

reload_colors() {
    pkill -USR1 -x kitty                     # kitty relê kitty.conf (inclui wallust.conf)
    pkill -USR2 -x waybar                    # waybar recarrega o style.css
    pkill -USR1 -x cava                      # cava recarrega config/tema
    swaync-client -rs >/dev/null 2>&1        # swaync relê o style.css (importa swaync.css do wallust)
    [ -f "$CACHE/hyprland.lua" ] && hyprctl eval "dofile('$CACHE/hyprland.lua')" >/dev/null
    systemctl --user try-restart swayosd.service    # swayosd só lê o style.css ao iniciar
    systemctl --user try-restart hyprshell.service  # hyprshell lê styles.css ao iniciar
    # wofi e hyprlock leem as cores sempre que abrem, não precisam de reload.
}

# Cores do rice a partir da imagem. Papel de parede claro gera tema claro (light16), escuro
# gera tema escuro (dark16). Se o fundo da imagem for de uma cor só (desenho/mangá em fundo
# liso), essa cor vira exatamente o fundo do tema: terminal, barra e apps ficam com o mesmo
# fundo do papel de parede. Os apps GTK3/GTK4 recebem as cores pelo tema-gtk4.py, os apps
# Qt/KDE pelo tema-qt.py (Kvantum "Wallust") e o claro/escuro pelo color-scheme do sistema.
gerar_cores() {
    local MODO=escuro FUNDO= paleta=dark16
    eval "$(python3 "$HOME/.config/hypr/scripts/analisar-papel.py" "$1")"
    [ "$MODO" = claro ] && paleta=light16
    wallust run -q -s -p "$paleta" "$1" || return 1
    if [ -n "$FUNDO" ] && [ -f "$CACHE/pywal.json" ]; then
        python3 - "$CACHE/pywal.json" "$FUNDO" "$CACHE/pywal-fundo.json" <<'EOF'
import json, sys
paleta = json.load(open(sys.argv[1]))
paleta["special"]["background"] = sys.argv[2]
# Ao fixar uma cor de fundo extraída das bordas, preserve contraste legível
# mesmo quando a imagem quase não tem variação tonal (por exemplo, fundo branco).
rgb = tuple(int(sys.argv[2].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
luminancia = sum(p * peso for p, peso in zip(rgb, (0.299, 0.587, 0.114)))
paleta["special"]["foreground"] = "#202124" if luminancia >= 140 else "#E6E6E6"
json.dump(paleta, open(sys.argv[3], "w"), indent=2)
EOF
        wallust cs -q -s -f pywal "$CACHE/pywal-fundo.json" || return 1
        # o "cs" troca {{wallpaper}} pelo caminho do arquivo de cores; a tela de bloqueio precisa da imagem
        sed -i "s|^\$wallpaper = .*|\$wallpaper = $1|" "$CACHE/hyprlock.conf"
    fi
    python3 "$HOME/.config/hypr/scripts/ajustar-contraste-terminal.py" "$MODO"
    python3 "$HOME/.config/hypr/scripts/tema-gtk4.py"
    python3 "$HOME/.config/hypr/scripts/tema-qt.py" "$MODO"
    python3 "$HOME/.config/hypr/scripts/tema-firefox.py"
    python3 "$HOME/.config/hypr/scripts/tema-obsidian.py"
    python3 "$HOME/.config/hypr/scripts/tema-spotify.py"
    tema_gtk3 "$MODO"
}

# GTK3: tema adw-gtk3 (claro ou escuro) com as cores do ~/.config/gtk-3.0/gtk.css. Sem ele
# instalado, cai no Adwaita. Ícones Tela no tom certo para o modo.
tema_gtk3() {
    local esquema=prefer-dark tema=adw-gtk3-dark escuro=1 icones=Tela-circle-black-dark
    if [ "$1" = claro ]; then
        esquema=prefer-light tema=adw-gtk3 escuro=0 icones=Tela-circle-black
    fi
    if [ ! -d /usr/share/themes/adw-gtk3 ] && [ ! -d "$HOME/.local/share/themes/adw-gtk3" ]; then
        tema=Adwaita; [ "$escuro" = 1 ] && tema=Adwaita-dark
    fi
    mkdir -p "$HOME/.config/gtk-3.0"
    if [ ! -f "$HOME/.config/gtk-3.0/settings.ini" ]; then
        cat > "$HOME/.config/gtk-3.0/settings.ini" <<EOF
[Settings]
gtk-theme-name=$tema
gtk-icon-theme-name=$icones
gtk-application-prefer-dark-theme=$escuro
EOF
    fi
    gsettings set org.gnome.desktop.interface color-scheme "$esquema"
    gsettings set org.gnome.desktop.interface gtk-theme "$tema"
    gsettings set org.gnome.desktop.interface icon-theme "$icones"
    sed -i -e "s/^gtk-theme-name=.*/gtk-theme-name=$tema/" \
           -e "s/^gtk-icon-theme-name=.*/gtk-icon-theme-name=$icones/" \
           -e "s/^gtk-application-prefer-dark-theme=.*/gtk-application-prefer-dark-theme=$escuro/" \
           "$HOME/.config/gtk-3.0/settings.ini"
}

case "$1" in
    --pick)   img="$(pick)" ;;
    --random) img="$(random_image)" ;;
    --reload) reload_colors; exit 0 ;;
    "")       echo "Uso: $(basename "$0") <imagem> | --pick | --random | --reload" >&2; exit 1 ;;
    *)        img="$1" ;;
esac

[ -z "$img" ] && exit 0                              # wofi cancelado
[ -f "$img" ] || img="$WALL_DIR/$img"                # wofi devolveu só o nome
if [ ! -f "$img" ]; then
    notify-send -u critical "Papel de parede" "Arquivo não encontrado: $img"
    exit 1
fi
img="$(readlink -f "$img")"

# Se a imagem escolhida for de um dos ricings (themes.tsv), aplica o ricing completo
theme_slug="$(theme_slug_for_image "$img")"
if [ -n "$theme_slug" ]; then
    exec "$HOME/.config/hypr/scripts/tema.sh" "$theme_slug"
fi
rm -f "$CURRENT_THEME"

# Garante o daemon do awww rodando
if ! awww query >/dev/null 2>&1; then
    awww-daemon >/dev/null 2>&1 &
    for _ in $(seq 20); do awww query >/dev/null 2>&1 && break; sleep 0.1; done
fi

awww img "$img" \
    --transition-type "$TRANSITION" \
    --transition-duration "$TRANSITION_DURATION" \
    --transition-fps 60 &

mkdir -p "$CACHE"
ln -sfn "$img" "$CURRENT"

gerar_cores "$img" && reload_colors
wait

notify-send -i "$img" "Papel de parede" "$(basename "$img")"
