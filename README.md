# Hyprland Material/Wallust Dotfiles

Dotfiles do meu ambiente **Hyprland (Lua API `hl.*`)** com paleta dinâmica via **Wallust** (tema escuro aconchegante em tons terrosos/dourados extraídos do papel de parede ativo `malboro-car.png`).

> **Privacidade:** este repositório contém apenas arquivos visuais, scripts do desktop, cores e papel de parede. Nenhuma chave de API, token, variável de ambiente (`export`), arquivo `.env`, e-mail pessoal ou dado privado é incluído.

---

## Paleta Ativa (Wallust)

Extraída automaticamente de [`wallpapers/malboro-car.png`](wallpapers/malboro-car.png) e preservada em [`colors/wallust/`](colors/wallust/):

| Token | Hex | Uso principal |
|---|---|---|
| `background` | `#171615` | Superfície base (Kitty, Waybar, SwayNC, Wofi, btop) |
| `foreground` | `#EED8D2` | Texto principal |
| `cursor` | `#A99F95` | Cursor do terminal |
| `color4` (`accent`) | `#967F3A` | Borda ativa Hyprland, workspace ativo, acento Material |
| `color6` (`accent2`) | `#A57B6E` | Gradiente de borda e links externos |
| `color8` (`muted`) | `#9C867F` | Borda inativa e elementos secundários |

---

## Destaques do Ricing

- **Hyprland (`hyprland.lua` + `input-desk.lua`):** bordas com gradiente Wallust, cantos arredondados (`rounding = 14`), blur e sombra suave, perfil de mouse preciso (`accel_profile = "flat"`, `sensitivity = 0.15`), alternância de layout US/BR ABNT2 (`Alt + Shift`), gestor de telas em `F8`, luz noturna gradual e modo preto-e-branco por shader GLSL (`grayscale.frag` / `grayscale_v2.frag`).
- **Waybar Material Design 3 (`config/waybar/`):**
  - Pílulas arredondadas seguindo `colors.css` do Wallust;
  - Daemon reativo [`hypr-state.py`](config/waybar/scripts/hypr-state.py) conectado ao socket Hyprland para atualizar workspaces abertos, focados e título da janela sem flicker;
  - Mini visualizador [`cava-mini.py`](config/waybar/scripts/cava-mini.py) + faixa em reprodução no centro da barra.
- **CAVA no Papel de Parede (`bin/cava-fundo-manager` + `config/cava/config-fundo`):** instância `kitten panel` por monitor com densidade automática de barras (`bars = 0`, `sensitivity = 145`), roteamento automático para a saída de áudio ativa (`bin/cava-segue-som`) e integração às cores Wallust.
- **Animfetch Black Hole (`config/animfetch/`):** arte em pixels quad (`44x16`, 24 frames) de um buraco negro inspirada na paleta ativa e hook opcional para Zsh em [`shell/animfetch.zsh`](shell/animfetch.zsh).
- **Motor de Temas Automático (`config/hypr/scripts/`):** ao trocar papel de parede (`SUPER + W` ou `SUPER + SHIFT + W`), o `wallpaper.sh` detecta fundo claro/escuro/liso (`analisar-papel.py`), roda `wallust`, recalibra contraste WCAG no terminal (`ajustar-contraste-terminal.py`) e sincroniza GTK3/GTK4 (`tema-gtk4.py`), Qt/Kvantum/KDE (`tema-qt.py`), Firefox/Zen (`tema-firefox.py`), Obsidian (`tema-obsidian.py`), pastas de ícones (`tema-pastas.py`), Spicetify (`tema-spotify.py`), SwayNC, SwayOSD, Hyprshell e Wofi.

---

## Estrutura do Repositório

```text
├── bin/                   # Wrappers cava, cava-segue-som e daemon cava-fundo-manager
├── colors/wallust/        # Snapshot da paleta ativa (#171615 / #EED8D2 / #967F3A / #A57B6E)
├── config/
│   ├── animfetch/         # Config + frames pixel-art "blackhole"
│   ├── btop/              # Config e tema wallust.theme
│   ├── cava/              # Config normal, config-fundo (wallpaper) e tema wallust
│   ├── gtk-3.0/ & gtk-4.0/# Overrides CSS/INI dinâmicos
│   ├── hypr/              # hyprland.lua, hyprlock, hypridle, hyprsunset, shaders e scripts
│   ├── hyprshell/         # Alt+Tab switcher TOML + CSS
│   ├── kitty/             # kitty.conf + current-theme.conf + wallust.conf
│   ├── Kvantum/ & qt6ct/  # Tema Wallust para apps Qt/KDE
│   ├── swaync/            # Central de notificações + som-notificacao.sh
│   ├── swayosd/           # OSD de volume/brilho estilo pílula
│   ├── wallust/           # wallust.toml e templates Mustache
│   ├── waybar/            # Config, CSS MD3, hypr-state.py, cava-mini.py e media.py
│   └── wofi/              # Lançador e seletor de papel de parede
├── shell/animfetch.zsh    # Hook leve do animfetch (--once) sem exports de ambiente
├── systemd/user/          # Unidades cava-fundo, hyprshell, swaync e swayosd
├── wallpapers/            # malboro-car.png
└── install.sh             # Instalador idempotente com backup automático
```

---

## Principais Atalhos

| Atalho | Ação |
|---|---|
| `SUPER + Q` | Abrir terminal (`kitty`) |
| `SUPER + R` | Abrir lançador (`wofi --show drun`) |
| `SUPER + E` | Abrir gerenciador de arquivos (`nautilus`) |
| `SUPER + F` | Abrir navegador (`firefox`) |
| `SUPER + C` | Fechar janela ativa |
| `SUPER + V` / `P` / `J` | Flutuar / Pseudo-tile / Alternar split |
| `SUPER + Return` / `SHIFT + Return` | Tela cheia / Maximizar mantendo barra |
| `SUPER + W` / `SHIFT + W` | Escolher wallpaper (`wofi`) / Wallpaper aleatório |
| `SUPER + N` (e `←` / `→`) | Alternar ou ajustar luz noturna (`hyprsunset`) |
| `SUPER + ALT + B` | Alternar shader preto-e-branco no Hyprland |
| `SUPER + B` / `SHIFT + B` | Ocultar Waybar / Reiniciar Waybar |
| `SUPER + L` | Bloquear sessão (`hyprlock`) |
| `SUPER + SHIFT + V` | Histórico de clipboard (`cliphist` + `wofi`) |
| `Print` / `SUPER + Print` | Captura de região / monitor (`hyprshot`) |

---

## Dependências Recomendadas (Arch Linux)

```bash
# Base compositor & utilitários
sudo pacman -S hyprland waybar wofi kitty cava btop swaync \
  hyprlock hypridle hyprsunset wl-clipboard cliphist \
  playerctl brightnessctl pavucontrol blueman network-manager-applet \
  imagemagick python qt6ct kvantum ttf-jetbrains-mono-nerd noto-fonts

# AUR (ex.: paru / yay)
paru -S awww wallust animfetch-git swayosd-git hyprshot hyprshell \
  adw-gtk-theme bibata-cursor-theme
```

> Ajuste as linhas `hl.monitor(...)` em [`config/hypr/hyprland.lua`](config/hypr/hyprland.lua) conforme os nomes dos seus monitores (`eDP-1`, `HDMI-A-2`, etc.).

---

## Instalação

```bash
git clone https://github.com/deve-ayo/hyprland-dotfiles.git
cd hyprland-dotfiles

# Apenas instala arquivos com backup automático do que já existir em ~/.config:
./install.sh

# Ou instala e já aplica papel de parede, cores e serviços na sessão Hyprland ativa:
./install.sh --apply
```

Se quiser o `animfetch --once` ao abrir o terminal, adicione ao seu `~/.zshrc`:

```zsh
[ -f "$HOME/.config/zsh/animfetch.zsh" ] && source "$HOME/.config/zsh/animfetch.zsh"
```
