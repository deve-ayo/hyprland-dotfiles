# Cores do rice a partir do papel de parede

Quando você troca o papel de parede, o **wallust** tira uma paleta de 16 cores
da imagem e gera arquivos de cor para cada programa. Depois disso, o script
`wallpaper.sh` recarrega tudo sem precisar reiniciar nada.

```
imagem ──► awww (mostra o papel de parede com transição)
       └─► wallust (gera as cores) ──► kitty · waybar · wofi · dunst · bordas do Hyprland · hyprlock
```

---

## 1. Uso no dia a dia

| Atalho | O que faz |
|---|---|
| `SUPER + W` | Abre o wofi com miniaturas de `~/Pictures/wallpapers` para você escolher |
| `SUPER + SHIFT + W` | Sorteia um papel de parede diferente do atual |

Pelo terminal:

```bash
~/.config/hypr/scripts/wallpaper.sh ~/Downloads/foto.jpg   # qualquer imagem
~/.config/hypr/scripts/wallpaper.sh --pick                 # seletor no wofi
~/.config/hypr/scripts/wallpaper.sh --random               # aleatório
~/.config/hypr/scripts/wallpaper.sh --reload               # só recarrega as cores
```

**Adicionar papéis de parede:** é só copiar as imagens (`jpg`, `png`, `webp`,
`gif`) para `~/Pictures/wallpapers/`. Para usar outra pasta:
`WALL_DIR=~/outra/pasta wallpaper.sh --random`.

**Ao ligar o PC:** o `awww-daemon` volta com o último papel de parede e as
cores já estão salvas em disco. Não é preciso fazer nada.

---

## 2. Onde fica cada coisa

| Arquivo | Para que serve |
|---|---|
| `~/.config/hypr/scripts/wallpaper.sh` | O script que faz tudo |
| `~/.config/wallust/wallust.toml` | Configuração do wallust (paleta, templates) |
| `~/.config/wallust/templates/` | Moldes com as variáveis de cor |
| `~/.cache/wallust/current_wallpaper` | Link para o papel de parede atual |

Arquivos **gerados**. Não edite, porque são sobrescritos a cada troca:

| Gerado em | Usado por | Como é recarregado |
|---|---|---|
| `~/.cache/wallust/colors.css` | waybar e wofi (`@import` no `style.css`) | waybar: `SIGUSR2`. wofi: ao abrir |
| `~/.config/kitty/wallust.conf` | kitty (`include` no `kitty.conf`) | `SIGUSR1` e sequências de escape nos terminais abertos |
| `~/.cache/wallust/hyprland.lua` | bordas das janelas (`dofile` no `hyprland.lua`) | `hyprctl eval "dofile(...)"` |
| `~/.cache/wallust/hyprlock.conf` | hyprlock (`source =`) | ao bloquear a tela |
| `~/.config/dunst/dunstrc.d/99-wallust.conf` | notificações | `dunstctl reload` |
| `~/.config/gtk-4.0/gtk.css` e `~/.config/gtk-3.0/gtk.css` | apps GTK4/libadwaita e GTK3 com o tema adw-gtk3 (Firefox e Brave no "tema do sistema"); gerados pelo `tema-gtk4.py` | ao reabrir o app. Claro/escuro muda na hora (`gsettings color-scheme`) |
| `~/.config/Kvantum/Wallust/` | apps Qt/KDE (Dolphin, Okular, Ark, Gwenview, VLC). É o desenho do Orchis-BW com as cores do papel de parede; gerado pelo `tema-qt.py` | ao reabrir o app |
| `~/.local/share/color-schemes/Wallust.colors` e `~/.config/kdeglobals` | cores próprias dos apps KDE (seleção, links); `tema-qt.py` | ao reabrir o app |

---

## 3. Personalizar

### Mudar o estilo da paleta

Edite `~/.config/wallust/wallust.toml`:

```toml
palette = "dark16"    # opções: dark, dark16, harddark, softdark, light, light16, softlight...
backend = "fastresize" # se as cores ficarem estranhas, tente "kmeans" ou "wal"
```

Depois rode `wallust run "$(readlink ~/.cache/wallust/current_wallpaper)" && wallpaper.sh --reload`
para ver o resultado sem trocar a imagem.

Dica: `wallust run -p harddark imagem.jpg` testa uma paleta só uma vez, sem mudar o toml.

### Mudar a transição do papel de parede

No topo do `wallpaper.sh`:

```bash
TRANSITION="grow"          # simple, fade, wipe, wave, grow, center, outer, any, random...
TRANSITION_DURATION="1.2"  # segundos
```

### Trocar qual cor vai onde

As variáveis disponíveis são:

- `background`, `foreground`, `cursor`
- `color0` … `color15`. De 0 a 7 são as cores normais, de 8 a 15 as versões claras.
  Em geral, `color1` é a avermelhada e `color4` a azulada/destaque, mas
  isso depende da imagem.

- **Waybar / wofi** (CSS do GTK): use `@color4`, `@foreground` etc. direto no
  `style.css`. Para transparência: `alpha(@background, 0.7)`. Para clarear ou
  escurecer: `shade(@color4, 1.2)`.
- **Hyprland**: edite `templates/hyprland.lua`. Hoje a borda ativa é um
  degradê de `color4` para `color6`.
- **Hyprlock**: no `hyprlock.conf` estão disponíveis `$background`,
  `$foreground`, `$accent` (color4), `$accent2` (color6) e `$wallpaper`.
  Exemplo para usar o papel de parede desfocado como fundo da tela de bloqueio:
  ```
  background {
      path = $wallpaper
      blur_passes = 3
  }
  ```

### Sintaxe dos templates

Dentro de `~/.config/wallust/templates/*`:

| Escrita | Resultado |
|---|---|
| `{{color4}}` | `#5A7FA3` |
| `{{color4 \| strip}}` | `5A7FA3` (sem `#`, para o Hyprland/hyprlock) |
| `{{color4 \| rgb}}` | `90,127,163` |
| `{{color4 \| lighten(0.2)}}` | 20% mais clara |
| `{{color4 \| darken(0.2)}}` | 20% mais escura |
| `{{wallpaper}}` | caminho da imagem atual |

### Adicionar outro programa (ex.: btop, cava, Zed)

1. Crie o template em `~/.config/wallust/templates/`, por exemplo `btop.theme`, usando as variáveis.
2. Registre no `wallust.toml`:
   ```toml
   btop = { template = "btop.theme", target = "~/.config/btop/themes/wallust.theme" }
   ```
3. Se o programa precisar ser avisado da mudança, adicione o comando na função
   `reload_colors()` do `wallpaper.sh`.
4. Aponte o programa para o arquivo gerado. No btop, por exemplo, `color_theme = "wallust"`.

---

## 4. Problemas comuns

| Sintoma | Solução |
|---|---|
| Papel de parede não aparece | Veja se o daemon está rodando com `awww query`. Se não estiver, rode `awww-daemon &` |
| Cores não mudaram em algum programa | Rode `wallpaper.sh --reload`. Para o waybar, `SUPER+SHIFT+B` reinicia |
| Waybar sem estilo | O `~/.cache/wallust/colors.css` precisa existir. Rode `wallpaper.sh --random` |
| Texto ilegível | Deixe `check_contrast = true` ou tente `palette = "harddark"` |
| App Qt/KDE ainda escuro ou com outra cor | Feche **todas** as janelas dele (o Dolphin fica rodando como `dolphin --daemon`: `pkill -x dolphin`). Veja também se o app não tem esquema de cores próprio (no Dolphin: Configurações → Esquema de cores → Padrão) |
| App GTK3 ainda escuro | Precisa do pacote `adw-gtk-theme` e de sair e entrar na sessão (a variável `GTK_THEME` antiga fica nos apps abertos até lá). Backup do antes: `~/.config/ricing-backup-2026-10-06-qt/` |
| Quero voltar ao P&B | Os backups estão em `~/.config/ricing-backup-2026-09-24/`. Copie de volta e troque `awww-daemon` por `hyprpaper` no `hyprland.lua` |

O modo P&B do botão da waybar (`toggle-bw.sh`, que usa um shader de tons de
cinza) continua funcionando normalmente por cima de tudo isso.
