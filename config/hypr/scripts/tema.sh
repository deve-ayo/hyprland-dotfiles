#!/bin/bash
# Troca o tema (ricing completo) + papel de parede correspondente.
#
# Uso:
#   tema.sh --pick          escolhe no wofi (com miniaturas)
#   tema.sh --next          avança para o próximo tema da lista
#   tema.sh --random        sorteia um tema diferente do atual
#   tema.sh --list          lista os temas disponíveis
#   tema.sh <slug|nome>     aplica o tema informado

THEMES_INDEX="$HOME/.config/hypr/themes/themes.tsv"
CACHE="$HOME/.cache/wallust"
CURRENT_WALL="$CACHE/current_wallpaper"
CURRENT_THEME="$CACHE/current_theme"

TRANSITION="${TRANSITION:-grow}"
TRANSITION_DURATION="${TRANSITION_DURATION:-1.2}"

if [ ! -f "$THEMES_INDEX" ]; then
    notify-send -u critical "Tema" "Índice não encontrado: $THEMES_INDEX"
    exit 1
fi

pick_theme() {
    local chosen
    chosen="$(
        while IFS=$'\t' read -r slug name kitty wall json; do
            printf 'img:%s:text:%s\n' "$wall" "$name"
        done < "$THEMES_INDEX" \
        | wofi --dmenu --allow-images --cache-file /dev/null --prompt "Tema" \
        | sed -E 's/^img:.*:text:(.*)$/\1/'
    )"
    [ -z "$chosen" ] && return 0
    awk -F'\t' -v target="$chosen" '$2 == target { print $1; exit }' "$THEMES_INDEX"
}

next_theme() {
    local cur=""
    [ -f "$CURRENT_THEME" ] && cur="$(cat "$CURRENT_THEME")"
    awk -F'\t' -v cur="$cur" '
        NR == 1 { first = $1 }
        found { print $1; exit 0 }
        $1 == cur { found = 1 }
        END { if (!found || cur == "") print first; else if (found && NR > 0 && !printed) {} }
    ' "$THEMES_INDEX" | head -n1
}

random_theme() {
    local cur=""
    [ -f "$CURRENT_THEME" ] && cur="$(cat "$CURRENT_THEME")"
    awk -F'\t' -v cur="$cur" '$1 != cur { print $1 }' "$THEMES_INDEX" | shuf -n1
}

resolve_theme() {
    local query="$1"
    awk -F'\t' -v q="$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]')" '
        tolower($1) == q || tolower($2) == q || tolower($3) == q { print $0; exit }
    ' "$THEMES_INDEX"
}

tema_gtk3_escuro() {
    local esquema=prefer-dark tema=adw-gtk3-dark escuro=1 icones=Tela-circle-black-dark
    if [ ! -d /usr/share/themes/adw-gtk3 ] && [ ! -d "$HOME/.local/share/themes/adw-gtk3" ]; then
        tema=Adwaita-dark
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

apply_theme() {
    local row slug name kitty wall json
    row="$(resolve_theme "$1")"
    if [ -z "$row" ]; then
        notify-send -u critical "Tema" "Tema não encontrado: $1"
        exit 1
    fi
    IFS=$'\t' read -r slug name kitty wall json <<< "$row"

    if ! awww query >/dev/null 2>&1; then
        awww-daemon >/dev/null 2>&1 &
        for _ in $(seq 20); do awww query >/dev/null 2>&1 && break; sleep 0.1; done
    fi

    awww img "$wall" \
        --transition-type "$TRANSITION" \
        --transition-duration "$TRANSITION_DURATION" \
        --transition-fps 60 &

    mkdir -p "$CACHE"
    ln -sfn "$wall" "$CURRENT_WALL"
    printf '%s\n' "$slug" > "$CURRENT_THEME"

    wallust cs -q -s -f pywal "$json" || exit 1
    sed -i "s|^\$wallpaper = .*|\$wallpaper = $wall|" "$CACHE/hyprlock.conf"
    python3 "$HOME/.config/hypr/scripts/ajustar-contraste-terminal.py" escuro

    python3 "$HOME/.config/hypr/scripts/tema-gtk4.py"
    python3 "$HOME/.config/hypr/scripts/tema-qt.py" escuro
    python3 "$HOME/.config/hypr/scripts/tema-firefox.py"
    python3 "$HOME/.config/hypr/scripts/tema-obsidian.py"
    python3 "$HOME/.config/hypr/scripts/tema-spotify.py"
    tema_gtk3_escuro
    python3 "$HOME/.config/hypr/scripts/tema-pastas.py"

    "$HOME/.config/hypr/scripts/wallpaper.sh" --reload
    wait

    notify-send -i "$wall" "Tema" "$name"
}

case "$1" in
    --pick)
        slug="$(pick_theme)"
        [ -z "$slug" ] && exit 0
        apply_theme "$slug"
        ;;
    --next|--cycle)
        cur=""
        [ -f "$CURRENT_THEME" ] && cur="$(cat "$CURRENT_THEME")"
        next="$(awk -F'\t' -v cur="$cur" '
            NR == 1 { first = $1 }
            take { print $1; done = 1; exit }
            $1 == cur { take = 1 }
            END { if (!done) print first }
        ' "$THEMES_INDEX")"
        apply_theme "$next"
        ;;
    --random)
        apply_theme "$(random_theme)"
        ;;
    --list)
        awk -F'\t' '{ printf "%-38s %s\n", $1, $2 }' "$THEMES_INDEX"
        ;;
    "")
        echo "Uso: $(basename "$0") --pick | --next | --random | --list | <tema>" >&2
        exit 1
        ;;
    *)
        apply_theme "$1"
        ;;
esac
