#!/bin/bash
STATE_FILE="/tmp/hypr-bw-mode-active"
SHADER="$HOME/.config/hypr/shaders/grayscale.frag"

if [ -f "$STATE_FILE" ]; then
    hyprctl --instance 0 eval 'hl.config({decoration = {screen_shader = ""}})'
    rm -f "$STATE_FILE"
else
    hyprctl --instance 0 eval "hl.config({decoration = {screen_shader = \"$SHADER\"}})"
    touch "$STATE_FILE"
fi
