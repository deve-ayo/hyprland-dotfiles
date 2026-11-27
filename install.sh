#!/usr/bin/env bash
set -euo pipefail

# Instalador portavel dos dotfiles Hyprland + Wallust.
# Faz backup de arquivos existentes antes de substituir e nao exporta segredos ou variaveis pessoais.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
APPLY_LIVE=false
BACKUP_USED=false

for arg in "$@"; do
    case "$arg" in
        --apply) APPLY_LIVE=true ;;
        -h|--help)
            cat <<EOF
Uso: $(basename "$0") [--apply]

Opcoes:
  --apply   Aplica o papel de parede e recarrega servicos/compositor na sessao ativa
  -h,--help Mostra esta ajuda
EOF
            exit 0
            ;;
        *)
            echo "Opcao desconhecida: $arg" >&2
            exit 1
            ;;
    esac
done

backup_and_copy() {
    local src="$1"
    local dst="$2"

    mkdir -p "$(dirname "$dst")"
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        if [ -f "$src" ] && [ -f "$dst" ] && [ ! -L "$dst" ] && cmp -s "$src" "$dst"; then
            return 0
        fi
        BACKUP_USED=true
        local rel="${dst#"$HOME/"}"
        mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
        mv "$dst" "$BACKUP_DIR/$rel"
    fi
    cp -a "$src" "$dst"
}

echo "[1/5] Instalando configuracoes (~/.config)..."
while IFS= read -r -d '' file; do
    rel="${file#"$REPO_DIR/config/"}"
    backup_and_copy "$file" "$HOME/.config/$rel"
done < <(find "$REPO_DIR/config" -type f -print0 | sort -z)

echo "[2/5] Instalando scripts em ~/.local/bin e servicos systemd..."
mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
while IFS= read -r -d '' file; do
    rel="${file#"$REPO_DIR/bin/"}"
    backup_and_copy "$file" "$HOME/.local/bin/$rel"
    chmod +x "$HOME/.local/bin/$rel"
done < <(find "$REPO_DIR/bin" -type f -print0 | sort -z)

while IFS= read -r -d '' file; do
    rel="${file#"$REPO_DIR/systemd/user/"}"
    backup_and_copy "$file" "$HOME/.config/systemd/user/$rel"
done < <(find "$REPO_DIR/systemd/user" -type f -print0 | sort -z)

echo "[3/5] Instalando papel de parede e paleta Wallust ativa..."
mkdir -p "$HOME/Pictures/wallpapers" "$HOME/.cache/wallust"
WALL_DEST="$HOME/Pictures/wallpapers/malboro-car.png"
backup_and_copy "$REPO_DIR/wallpapers/malboro-car.png" "$WALL_DEST"

while IFS= read -r -d '' file; do
    rel="${file#"$REPO_DIR/colors/wallust/"}"
    dest="$HOME/.cache/wallust/$rel"
    if [ "$rel" = "pywal.json" ] || [ "$rel" = "hyprlock.conf" ]; then
        if [ -f "$dest" ] && [ ! -L "$dest" ] && cmp -s <(sed "s|~/Pictures/wallpapers/malboro-car\\.png|$WALL_DEST|g" "$file") "$dest"; then
            continue
        fi
        backup_and_copy "$file" "$dest"
        sed -i "s|~/Pictures/wallpapers/malboro-car\\.png|$WALL_DEST|g" "$dest"
    else
        backup_and_copy "$file" "$dest"
    fi
done < <(find "$REPO_DIR/colors/wallust" -type f -print0 | sort -z)

ln -sfn "$WALL_DEST" "$HOME/.cache/wallust/current_wallpaper"

echo "[4/5] Instalando snippet do animfetch e ajustando permissoes..."
mkdir -p "$HOME/.config/zsh"
backup_and_copy "$REPO_DIR/shell/animfetch.zsh" "$HOME/.config/zsh/animfetch.zsh"

chmod +x "$HOME/.config/hypr/scripts/"*.sh "$HOME/.config/hypr/scripts/"*.py 2>/dev/null || true
chmod +x "$HOME/.config/waybar/scripts/"*.py 2>/dev/null || true
chmod +x "$HOME/.config/swaync/som-notificacao.sh" 2>/dev/null || true

if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

if [ "$APPLY_LIVE" = true ]; then
    echo "[5/5] Aplicando ricing na sessao atual..."
    if command -v awww >/dev/null 2>&1; then
        if ! awww query >/dev/null 2>&1; then
            awww-daemon >/dev/null 2>&1 &
            for _ in $(seq 20); do awww query >/dev/null 2>&1 && break; sleep 0.1; done
        fi
        awww img "$WALL_DEST" --transition-type grow --transition-duration 1.0 --transition-fps 60 || true
    fi
    [ -x "$HOME/.config/hypr/scripts/wallpaper.sh" ] && "$HOME/.config/hypr/scripts/wallpaper.sh" --reload || true
    if command -v systemctl >/dev/null 2>&1; then
        systemctl --user enable --now swaync.service swayosd.service hyprshell.service cava-fundo.service >/dev/null 2>&1 || true
        systemctl --user restart waybar.service >/dev/null 2>&1 || true
    fi
else
    echo "[5/5] Instalacao concluida (modo seguro, sem reiniciar sua sessao)."
fi

echo
if [ "$BACKUP_USED" = true ]; then
    echo "Backup dos arquivos anteriores salvo em: $BACKUP_DIR"
fi
echo "Para ativar o animfetch no Zsh, adicione esta linha ao ~/.zshrc:"
echo "  [ -f \"\$HOME/.config/zsh/animfetch.zsh\" ] && source \"\$HOME/.config/zsh/animfetch.zsh\""
echo
echo "Para habilitar os servicos do desktop e aplicar o papel de parede agora:"
echo "  systemctl --user enable --now swaync.service swayosd.service hyprshell.service cava-fundo.service"
echo "  \"$HOME/.config/hypr/scripts/wallpaper.sh\" \"$WALL_DEST\""
