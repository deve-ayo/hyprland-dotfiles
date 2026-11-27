#!/usr/bin/env python3
"""O que está tocando agora, no meio da barra de cima da waybar — venha de onde vier.

Escolha da fonte, em ordem:
  1. player MPRIS tocando (Firefox, Spotify, VLC...); o último escolhido tem preferência
  2. qualquer outro áudio saindo pelo PipeWire/Pulse (apps sem MPRIS, ex. Ayo Música)
  3. player MPRIS pausado
  4. "Nada tocando"

  media.py daemon       módulo custom/media-title (um JSON por linha). Grava capa e
                        botões em $XDG_RUNTIME_DIR/waybar-media/ e avisa a
                        waybar: SIGRTMIN+9 = capa, SIGRTMIN+10 = botões
  media.py ctl <cmd>    previous | play-pause | next no player que está sendo mostrado
"""
import hashlib
import html
import json
import os
import select
import signal
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SEP = "\x1f"
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
# Um diretório só: o módulo image não recebe WAYBAR_OUTPUT_NAME. Com a barra em dois
# monitores, os dois daemons gravam o mesmo conteúdo, sem problema.
STATE = RUNTIME / "waybar-media"
COVERS = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "waybar-covers"
NO_COVER = Path.home() / ".config/waybar/assets/sem-capa.png"
SIG_COVER = signal.SIGRTMIN + 9
SIG_BUTTONS = signal.SIGRTMIN + 10

ICON_PREV, ICON_NEXT = "\U000F04AE", "\U000F04AD"
ICON_PLAY, ICON_PAUSE = "\U000F040A", "\U000F03E4"

MPRIS_FIELDS = ["playerInstance", "playerName", "status", "xesam:title", "xesam:artist",
                "xesam:album", "mpris:artUrl"]
# media.name genéricos que não dizem nada sobre a música
GENERIC_NAMES = {"", "playback", "playback stream", "audio stream", "audiostream",
                 "audiocallbackdriver", "output", "simple dsp", "alsa playback",
                 "(null)"}  # o Firefox manda "(null)" quando a aba não informa título


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def mpris_players():
    fmt = SEP.join("{{%s}}" % f for f in MPRIS_FIELDS)
    players = []
    for line in run(["playerctl", "-a", "metadata", "--format", fmt]).splitlines():
        p = dict(zip(["instance", "name", "status", "title", "artist", "album", "art"],
                     line.split(SEP)))
        if p.get("instance") and p["instance"] != "playerctld":
            players.append(p)
    return players


def pulse_stream():
    """Primeiro áudio tocando (não pausado) que não seja som de evento do sistema."""
    try:
        streams = json.loads(run(["pactl", "-f", "json", "list", "sink-inputs"]) or "[]")
    except json.JSONDecodeError:
        return None
    for s in streams:
        props = s.get("properties", {})
        if s.get("corked") or props.get("media.role") in ("event", "phone"):
            continue
        app = props.get("application.name") or props.get("application.process.binary") or "Áudio"
        title = props.get("media.title") or ""
        name = props.get("media.name") or ""
        if not title and name.strip().lower() not in GENERIC_NAMES:
            title = name
        return {"title": title or app, "artist": props.get("media.artist", ""),
                "album": props.get("media.album", ""), "app": app}
    return None


def pretty(player_name):
    return player_name[:1].upper() + player_name[1:] if player_name else ""


class Media:
    def __init__(self):
        self.chosen = None     # instância MPRIS mostrada (fica fixa enquanto fizer sentido)
        self.last = {}

    def pick(self):
        players = mpris_players()
        by_inst = {p["instance"]: p for p in players}
        playing = [p for p in players if p["status"] == "Playing"]
        if self.chosen in by_inst and by_inst[self.chosen]["status"] == "Playing":
            return by_inst[self.chosen], None
        if playing:
            return playing[0], None
        stream = pulse_stream()
        if stream:
            return None, stream
        if self.chosen in by_inst:
            return by_inst[self.chosen], None
        return (players[0] if players else None), None

    def render(self):
        player, stream = self.pick()
        self.chosen = player["instance"] if player else None
        esc = html.escape

        if player:
            title = player["title"] or pretty(player["name"])
            text = title + (f" — {player['artist']}" if player["artist"] else "")
            info = [f"<b>{esc(title)}</b>"] + [esc(x) for x in (player["artist"], player["album"]) if x]
            info.append(f"\nOrigem: {esc(pretty(player['name']))}")
            status = player["status"]
            cls = "playing" if status == "Playing" else "paused"
        elif stream:
            text = stream["title"] + (f" — {stream['artist']}" if stream["artist"] else "")
            info = [f"<b>{esc(stream['title'])}</b>"] + [esc(x) for x in (stream["artist"], stream["album"]) if x]
            info.append(f"\nOrigem: {esc(stream['app'])} (sem controle de mídia)")
            status, cls = "Playing", "playing"
        else:
            text, info, status, cls = "Nada tocando", ["Nada tocando"], "", "idle"

        title_json = json.dumps({"text": esc(text), "tooltip": "\n".join(info), "class": cls},
                                ensure_ascii=False)

        can_control = player is not None
        def button(icon, tip):
            return json.dumps({"text": icon, "tooltip": tip if can_control else "Sem controle",
                               "class": ["media-button"] if can_control else ["media-button", "disabled"]},
                              ensure_ascii=False)
        buttons = {
            "player": self.chosen or "",
            "prev": button(ICON_PREV, "Anterior"),
            "play": button(ICON_PAUSE if status == "Playing" else ICON_PLAY,
                           "Pausar" if status == "Playing" else "Tocar"),
            "next": button(ICON_NEXT, "Próxima"),
        }
        cover_key = (player or {}).get("art", "") + SEP + text

        if title_json != self.last.get("title"):
            print(title_json, flush=True)
        if self.write(buttons):
            signal_waybar(SIG_BUTTONS)
        if cover_key != self.last.get("cover_key"):
            self.last["cover_key"] = cover_key
            path = cover_path(player["art"]) if player and player["art"] else None
            self.write({"cover": f"{path or NO_COVER}\n{esc(text)}"})
            signal_waybar(SIG_COVER)
        self.last["title"] = title_json

    def write(self, files):
        changed = False
        for name, data in files.items():
            if self.last.get(name) == data:
                continue
            self.last[name] = data
            tmp = STATE / f".{name}.tmp"
            tmp.write_text(data + "\n")
            tmp.replace(STATE / name)
            changed = True
        return changed


def cover_path(art):
    """Miniatura quadrada da capa. A waybar carrega a imagem na thread da interface,
    então uma capa enorme (ou num formato que o GdkPixbuf não lê) nunca vai direto."""
    path = fetch(art)
    if not path:
        return None
    try:
        from PIL import Image
        st = path.stat()
        thumb = COVERS / f"thumb-{hashlib.md5(f'{path}{st.st_mtime}{st.st_size}'.encode()).hexdigest()}.png"
        if not thumb.is_file():
            with Image.open(path) as im:
                im.draft("RGB", (192, 192))  # JPEG decodifica já reduzido
                im = im.convert("RGBA")
                side = min(im.size)
                left, top = (im.width - side) // 2, (im.height - side) // 2
                im = im.crop((left, top, left + side, top + side))
                im.thumbnail((96, 96))
                COVERS.mkdir(parents=True, exist_ok=True)
                im.save(thumb)
        return thumb
    except Exception:
        return None


def fetch(art):
    if art.startswith("file://"):
        path = Path(urllib.parse.unquote(art[7:]))
        return path if path.is_file() else None
    if art.startswith(("http://", "https://")):
        COVERS.mkdir(parents=True, exist_ok=True)
        path = COVERS / hashlib.md5(art.encode()).hexdigest()
        if not path.is_file():
            try:
                with urllib.request.urlopen(art, timeout=5) as r:
                    path.write_bytes(r.read())
            except OSError:
                return None
            old = sorted(COVERS.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)[50:]
            for f in old:
                f.unlink(missing_ok=True)
        return path
    return None


def signal_waybar(sig):
    for proc in Path("/proc").iterdir():
        if proc.name.isdigit():
            try:
                if (proc / "comm").read_text().strip() == "waybar":
                    os.kill(int(proc.name), sig)
            except OSError:
                pass


WATCHERS = {
    # qualquer mudança em qualquer player MPRIS (inclusive quando ele fecha)
    "mpris": ["playerctl", "-a", "--follow", "metadata", "--format",
              "{{playerInstance}}{{status}}{{xesam:title}}{{xesam:artist}}{{mpris:artUrl}}"],
    # streams de áudio abrindo, fechando, pausando ou mudando de título
    "pulse": ["pactl", "subscribe"],
}


def daemon():
    STATE.mkdir(parents=True, exist_ok=True)
    media = Media()
    procs = {}

    def stop(*_):
        for p in procs.values():
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGPIPE, stop)  # waybar fechou nosso stdout

    def spawn(key):
        procs[key] = subprocess.Popen(WATCHERS[key], stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, text=True, bufsize=1)

    for key in WATCHERS:
        spawn(key)
    media.render()
    while True:
        by_fd = {p.stdout: k for k, p in procs.items()}
        relevant, timeout = False, None
        while True:
            ready, _, _ = select.select(list(by_fd), [], [], timeout)
            if not ready:
                break
            for f in ready:
                line = f.readline()
                key = by_fd[f]
                if not line:  # watcher morreu (ex. PipeWire reiniciou): recria
                    procs[key].wait()
                    spawn(key)
                    by_fd = {p.stdout: k for k, p in procs.items()}
                    relevant = True
                elif key == "mpris" or "sink-input" in line:
                    relevant = True
            if relevant:
                timeout = 0.08  # junta a rajada de eventos
        media.render()


def ctl(cmd):
    try:
        player = (STATE / "player").read_text().strip()
    except OSError:
        return
    if player:
        subprocess.run(["playerctl", "-p", player, cmd])


if __name__ == "__main__":
    if sys.argv[1:2] == ["daemon"]:
        try:
            daemon()
        except BrokenPipeError:
            sys.exit(0)
    elif sys.argv[1:2] == ["ctl"] and len(sys.argv) == 3:
        ctl(sys.argv[2])
    else:
        sys.exit(__doc__)
