#!/usr/bin/env python3
"""Garante contraste legível (WCAG AA) nas paletas de terminal geradas pelo wallust.

Corrige dois problemas comuns em ricings automáticos:
1. Fundos cinza-médio (ex.: mangás/artes em tons médios como #797979), onde nem branco
   nem preto alcançam contraste confortável no terminal translúcido.
2. Cores ANSI (color1..color15 e principalmente color8/comentários/citações) que ficam
   com luminância próxima à do fundo, tornando textos, códigos inline e sugestões invisíveis
   (inclusive sob o shader P&B do Hyprland).

Atualiza ~/.config/kitty/wallust.conf, ~/.cache/wallust/foot.ini e ~/.config/btop/themes/wallust.theme.
"""
import colorsys
import os
import re
import sys


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, round(rgb[0]))),
        max(0, min(255, round(rgb[1]))),
        max(0, min(255, round(rgb[2]))),
    )


def rel_lum(rgb: tuple[int, int, int]) -> float:
    lin = []
    for c in rgb:
        v = c / 255.0
        lin.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    l1, l2 = rel_lum(rgb1), rel_lum(rgb2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def set_lightness(rgb: tuple[int, int, int], new_l: float) -> tuple[int, int, int]:
    h, _l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    new_l = max(0.0, min(1.0, new_l))
    r, g, b = colorsys.hls_to_rgb(h, new_l, s)
    return (round(r * 255), round(g * 255), round(b * 255))


def adjust_to_lum(rgb: tuple[int, int, int], target_lum: float) -> tuple[int, int, int]:
    lo, hi = 0.0, 1.0
    for _ in range(26):
        mid = (lo + hi) / 2.0
        cand = set_lightness(rgb, mid)
        if rel_lum(cand) < target_lum:
            lo = mid
        else:
            hi = mid
    return set_lightness(rgb, (lo + hi) / 2.0)


def ensure_contrast(
    rgb: tuple[int, int, int],
    bg: tuple[int, int, int],
    is_dark: bool,
    min_cr: float,
    max_cr: float | None = None,
) -> tuple[int, int, int]:
    cur_cr = contrast(rgb, bg)
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

    # Se a cor estiver do lado errado do fundo (ex.: muito escura num tema escuro),
    # busca no intervalo completo rumo ao extremo legível.
    if cur_cr < min_cr:
        if is_dark:
            lo, hi = (l if rel_lum(rgb) >= rel_lum(bg) else 0.0), 0.985
            for _ in range(26):
                mid = (lo + hi) / 2.0
                cand = set_lightness(rgb, mid)
                if contrast(cand, bg) < min_cr:
                    lo = mid
                else:
                    hi = mid
            return set_lightness(rgb, hi)
        else:
            lo, hi = 0.015, (l if rel_lum(rgb) <= rel_lum(bg) else 1.0)
            for _ in range(26):
                mid = (lo + hi) / 2.0
                cand = set_lightness(rgb, mid)
                if contrast(cand, bg) < min_cr:
                    hi = mid
                else:
                    lo = mid
            return set_lightness(rgb, lo)

    if max_cr is not None and cur_cr > max_cr:
        bg_l = colorsys.rgb_to_hls(bg[0] / 255.0, bg[1] / 255.0, bg[2] / 255.0)[1]
        if is_dark:
            lo, hi = bg_l, l
            for _ in range(26):
                mid = (lo + hi) / 2.0
                cand = set_lightness(rgb, mid)
                if contrast(cand, bg) > max_cr:
                    hi = mid
                else:
                    lo = mid
            return set_lightness(rgb, lo)
        else:
            lo, hi = l, bg_l
            for _ in range(26):
                mid = (lo + hi) / 2.0
                cand = set_lightness(rgb, mid)
                if contrast(cand, bg) > max_cr:
                    lo = mid
                else:
                    hi = mid
            return set_lightness(rgb, hi)

    return rgb


def parse_kitty_conf(path: str) -> dict[str, str]:
    kv = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*([a-zA-Z0-9_]+)\s+(#[0-9a-fA-F]{6})\b", line)
            if m:
                kv[m.group(1)] = m.group(2).upper()
    return kv


def main() -> int:
    modo_arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    kitty_path = os.path.expanduser("~/.config/kitty/wallust.conf")
    foot_path = os.path.expanduser("~/.cache/wallust/foot.ini")
    btop_path = os.path.expanduser("~/.config/btop/themes/wallust.theme")
    animfetch_path = os.path.expanduser("~/.cache/wallust/animfetch-colors.json")
    hyprshell_css = os.path.expanduser("~/.config/hyprshell/styles.css")

    if not os.path.isfile(kitty_path):
        return 0

    kv = parse_kitty_conf(kitty_path)
    if "background" not in kv or "foreground" not in kv:
        return 0

    orig_bg = hex_to_rgb(kv["background"])
    orig_fg = hex_to_rgb(kv["foreground"])

    if modo_arg in ("escuro", "dark"):
        is_dark = True
    elif modo_arg in ("claro", "light"):
        is_dark = False
    else:
        is_dark = rel_lum(orig_fg) >= rel_lum(orig_bg)

    # 1. Tira o fundo da "zona morta" de cinza médio (onde nem branco nem preto têm contraste >= 4.5:1)
    bg = orig_bg
    bg_lum = rel_lum(bg)
    if is_dark and bg_lum > 0.046:
        # Ex.: #797979 (L=0.191) -> ~#313131 (L=0.030), preservando matiz/saturação
        bg = adjust_to_lum(bg, 0.030)
    elif (not is_dark) and bg_lum < 0.62:
        bg = adjust_to_lum(bg, 0.68)

    # 2. Foreground principal bem nítido (WCAG AAA >= 8.0:1)
    fg = ensure_contrast(orig_fg, bg, is_dark, min_cr=8.0)

    # 3. Detecta se a paleta é monocromática (saturação muito baixa em color1..color6)
    sats = []
    for i in range(1, 7):
        k = f"color{i}"
        if k in kv:
            c = hex_to_rgb(kv[k])
            sats.append(colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)[2])
    is_mono = (max(sats) if sats else 0.0) < 0.06

    new_colors: dict[str, tuple[int, int, int]] = {}

    # color0: superfície próxima ao fundo (mantém blocos/badges de TUIs legíveis)
    if "color0" in kv:
        bg_l = colorsys.rgb_to_hls(bg[0] / 255.0, bg[1] / 255.0, bg[2] / 255.0)[1]
        if is_dark:
            c0_l = bg_l - 0.05 if bg_l >= 0.08 else bg_l + 0.05
        else:
            c0_l = bg_l - 0.06 if bg_l >= 0.12 else bg_l + 0.06
        new_colors["color0"] = set_lightness(bg, c0_l)

    # color8: texto secundário / comentários / citações / autosuggestions
    # Contraste entre 4.0:1 e 5.2:1 (sempre legível até com dim_opacity, mas ainda discreto)
    if "color8" in kv:
        new_colors["color8"] = ensure_contrast(hex_to_rgb(kv["color8"]), bg, is_dark, min_cr=4.0, max_cr=5.2)

    # color1..color6: cores ANSI normais (escada tonal suave se monocromático)
    mono_targets = [4.7, 5.1, 5.5, 5.9, 6.3, 6.8]
    for i in range(1, 7):
        k = f"color{i}"
        if k in kv:
            target = mono_targets[i - 1] if is_mono else 4.6
            new_colors[k] = ensure_contrast(hex_to_rgb(kv[k]), bg, is_dark, min_cr=target)

    # color9..color14: variantes brilhantes (pelo menos tão legíveis quanto color1..6)
    for i in range(9, 15):
        k = f"color{i}"
        base_k = f"color{i - 8}"
        if k in kv:
            base_cr = contrast(new_colors.get(base_k, bg), bg)
            target = min(8.5, max(5.2, base_cr + (0.6 if is_mono else 0.3)))
            new_colors[k] = ensure_contrast(hex_to_rgb(kv[k]), bg, is_dark, min_cr=target)

    # color7 e color15: texto claro/escuro de alto contraste
    if "color7" in kv:
        new_colors["color7"] = ensure_contrast(hex_to_rgb(kv["color7"]), bg, is_dark, min_cr=7.2)
    if "color15" in kv:
        new_colors["color15"] = ensure_contrast(hex_to_rgb(kv["color15"]), bg, is_dark, min_cr=8.5)

    cursor_rgb = ensure_contrast(hex_to_rgb(kv.get("cursor", kv["foreground"])), bg, is_dark, min_cr=5.5)
    sel_bg = new_colors.get("color4", fg)
    sel_fg = bg
    url_rgb = new_colors.get("color6", fg)
    active_border = new_colors.get("color4", fg)
    inactive_border = new_colors.get("color8", bg)

    # Reescreve ~/.config/kitty/wallust.conf
    kitty_lines = [
        "# Gerado pelo wallust + ajuste automático de contraste WCAG.",
        f"foreground {rgb_to_hex(fg)}",
        f"background {rgb_to_hex(bg)}",
        f"cursor {rgb_to_hex(cursor_rgb)}",
        f"selection_foreground {rgb_to_hex(sel_fg)}",
        f"selection_background {rgb_to_hex(sel_bg)}",
        f"active_border_color {rgb_to_hex(active_border)}",
        f"inactive_border_color {rgb_to_hex(inactive_border)}",
        f"url_color {rgb_to_hex(url_rgb)}",
        "dim_opacity 0.75",
        "",
    ]
    for i in range(16):
        k = f"color{i}"
        if k in new_colors:
            kitty_lines.append(f"{k:<7} {rgb_to_hex(new_colors[k])}")

    with open(kitty_path, "w", encoding="utf-8") as f:
        f.write("\n".join(kitty_lines) + "\n")

    # Reescreve ~/.cache/wallust/foot.ini se existir
    if os.path.isfile(foot_path):
        foot_lines = [
            "# Gerado pelo wallust + ajuste automático de contraste WCAG.",
            "[colors-dark]",
            f"foreground={rgb_to_hex(fg)[1:]}",
            f"background={rgb_to_hex(bg)[1:]}",
        ]
        for i in range(8):
            if f"color{i}" in new_colors:
                foot_lines.append(f"regular{i}={rgb_to_hex(new_colors[f'color{i}'])[1:]}")
        for i in range(8):
            if f"color{i+8}" in new_colors:
                foot_lines.append(f"bright{i}={rgb_to_hex(new_colors[f'color{i+8}'])[1:]}")
        foot_lines.append("alpha=0.92")
        with open(foot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(foot_lines) + "\n")

    # Reescreve ~/.config/btop/themes/wallust.theme se existir
    if os.path.isfile(btop_path):
        c1 = rgb_to_hex(new_colors.get("color1", fg))
        c2 = rgb_to_hex(new_colors.get("color2", fg))
        c3 = rgb_to_hex(new_colors.get("color3", fg))
        c4 = rgb_to_hex(new_colors.get("color4", fg))
        c5 = rgb_to_hex(new_colors.get("color5", fg))
        c6 = rgb_to_hex(new_colors.get("color6", fg))
        c8 = rgb_to_hex(new_colors.get("color8", fg))
        bgh = rgb_to_hex(bg)
        fgh = rgb_to_hex(fg)
        btop_content = f"""# Gerado pelo wallust + ajuste automático de contraste WCAG.
theme[main_bg]="{bgh}"
theme[main_fg]="{fgh}"
theme[title]="{fgh}"
theme[hi_fg]="{c4}"
theme[selected_bg]="{c4}"
theme[selected_fg]="{bgh}"
theme[followed_bg]="{c5}"
theme[followed_fg]="{bgh}"
theme[inactive_fg]="{c8}"
theme[graph_text]="{fgh}"
theme[meter_bg]="{c8}"
theme[proc_misc]="{c5}"
theme[proc_follow_bg]="{c5}"
theme[proc_pause_bg]="{c3}"
theme[proc_banner_bg]="{c4}"
theme[proc_banner_fg]="{bgh}"

theme[cpu_box]="{c4}"
theme[mem_box]="{c2}"
theme[net_box]="{c1}"
theme[proc_box]="{c6}"
theme[div_line]="{c8}"

theme[temp_start]="{c4}"
theme[temp_mid]="{c3}"
theme[temp_end]="{c1}"

theme[cpu_start]="{c4}"
theme[cpu_mid]="{c6}"
theme[cpu_end]="{c2}"

theme[free_start]="{c2}"
theme[free_mid]="{c3}"
theme[free_end]="{c1}"

theme[cached_start]="{c6}"
theme[cached_mid]="{c4}"
theme[cached_end]="{c5}"

theme[available_start]="{c2}"
theme[available_mid]="{c6}"
theme[available_end]="{c4}"

theme[used_start]="{c3}"
theme[used_mid]="{c5}"
theme[used_end]="{c1}"

theme[download_start]="{c6}"
theme[download_mid]="{c4}"
theme[download_end]="{c2}"

theme[upload_start]="{c5}"
theme[upload_mid]="{c3}"
theme[upload_end]="{c1}"
"""
        with open(btop_path, "w", encoding="utf-8") as f:
            f.write(btop_content)

    # Salva paleta já com contraste corrigido para o animfetch seguir o tema com nitidez
    os.makedirs(os.path.dirname(animfetch_path), exist_ok=True)
    colors_hex = {f"color{i}": rgb_to_hex(new_colors[f"color{i}"]) for i in range(16) if f"color{i}" in new_colors}
    anim_payload = {
        "special": {
            "background": rgb_to_hex(bg),
            "foreground": rgb_to_hex(fg),
            "cursor": rgb_to_hex(cursor_rgb),
        },
        "colors": colors_hex,
        **colors_hex,
        "foreground": rgb_to_hex(fg),
        "background": rgb_to_hex(bg),
    }
    import json
    with open(animfetch_path, "w", encoding="utf-8") as f:
        json.dump(anim_payload, f, indent=2)

    # Atualiza as cores do Alt+Tab (hyprshell) para seguir o ricing atual
    if os.path.isdir(os.path.dirname(hyprshell_css)):
        c0 = new_colors.get("color0", bg)
        c4 = new_colors.get("color4", fg)
        c8 = new_colors.get("color8", fg)
        hs_css = f"""/* Gerado automaticamente pelo ricing (wallust + contraste WCAG) */
:root {{
    --border-color: rgba({c8[0]}, {c8[1]}, {c8[2]}, 0.55);
    --border-color-active: rgba({c4[0]}, {c4[1]}, {c4[2]}, 1);

    --bg-color: rgba({bg[0]}, {bg[1]}, {bg[2]}, 0.94);
    --bg-color-hover: rgba({c0[0]}, {c0[1]}, {c0[2]}, 0.96);

    --border-radius: 20px;
    --border-size: 2px;
    --border-style: solid;

    --text-color: rgba({fg[0]}, {fg[1]}, {fg[2]}, 1);

    --window-padding: 6px;
    --bg-window-color: rgba({c0[0]}, {c0[1]}, {c0[2]}, 0.92);
}}
"""
        with open(hyprshell_css, "w", encoding="utf-8") as f:
            f.write(hs_css)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
