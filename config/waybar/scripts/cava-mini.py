#!/usr/bin/env python3
"""Mini CAVA para o centro da Waybar com animação de troca de música.

- Quando não há áudio tocando, fica oculto (ou discreto) sem consumir CPU (sleep_timer).
- Quando há música tocando, exibe 10 barras animadas em tempo real (▁▂▃▄▅▆▇█).
- Toda vez que a música muda, expande suavemente exibindo o título (e artista) por
  alguns segundos e depois recolhe de volta para o mini cava.
"""
import html
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time

BARS = 10
CHARS = " ▁▂▃▄▅▆▇█"
ANNOUNCE_SEC = 4.2
EXPAND_SEC = 0.35
COLLAPSE_SEC = 0.35

CAVA_CFG = f"""[general]
framerate = 24
autosens = 1
bars = {BARS}
lower_cutoff_freq = 50
higher_cutoff_freq = 10000
sleep_timer = 1

[input]
method = pipewire
source = auto
active = 0
remix = 1
virtual = 1

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 8
bar_delimiter = 59
frame_delimiter = 10
show_idle_bar_heads = 0

[smoothing]
monstercat = 1
noise_reduction = 75
"""

GENERIC_NAMES = {
    "", "playback", "playback stream", "audio stream", "audiostream",
    "audiocallbackdriver", "output", "simple dsp", "alsa playback", "(null)",
}


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=1.5)
    except Exception:
        return ""


def current_track():
    fmt = "{{playerInstance}}\x1f{{playerName}}\x1f{{status}}\x1f{{xesam:title}}\x1f{{xesam:artist}}"
    out = run_cmd(["playerctl", "-a", "metadata", "--format", fmt])
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 5:
            continue
        inst, name, status, title, artist = parts[:5]
        if inst == "playerctld" or status != "Playing":
            continue
        title = title.strip() or name.strip()
        artist = artist.strip()
        label = f"{title} — {artist}" if artist else title
        return label, title, artist, name.strip()

    # Fallback: stream PipeWire/Pulse ativo (ex.: apps sem MPRIS)
    raw = run_cmd(["pactl", "-f", "json", "list", "sink-inputs"])
    if raw:
        try:
            for s in json.loads(raw):
                props = s.get("properties", {})
                if s.get("corked") or props.get("media.role") in ("event", "phone"):
                    continue
                app = props.get("application.name") or props.get("application.process.binary") or "Áudio"
                title = (props.get("media.title") or "").strip()
                mname = (props.get("media.name") or "").strip()
                if not title and mname.lower() not in GENERIC_NAMES:
                    title = mname
                artist = (props.get("media.artist") or "").strip()
                label = f"{title} — {artist}" if (title and artist) else (title or app)
                return label, (title or app), artist, app
        except Exception:
            pass
    return "", "", "", ""


class MiniCava:
    def __init__(self):
        self.lock = threading.Lock()
        self.track_label = ""
        self.track_tooltip = ""
        self.playing = False
        self.announce_start = 0.0
        self.last_announced = ""
        self.stop_ev = threading.Event()

    def refresh_track(self):
        label, title, artist, source = current_track()
        with self.lock:
            now = time.monotonic()
            if label:
                self.playing = True
                if label != self.last_announced:
                    self.last_announced = label
                    self.announce_start = now
                self.track_label = label
                src_pretty = source[:1].upper() + source[1:] if source else ""
                tip_lines = [f"<b>{html.escape(title)}</b>"]
                if artist:
                    tip_lines.append(html.escape(artist))
                if src_pretty:
                    tip_lines.append(f"Fonte: {html.escape(src_pretty)}")
                self.track_tooltip = "\n".join(tip_lines)
            else:
                self.playing = False
                self.track_label = ""
                self.track_tooltip = "Nada tocando"

    def watch_media(self):
        self.refresh_track()
        while not self.stop_ev.is_set():
            p_mpris = subprocess.Popen(
                ["playerctl", "-a", "--follow", "metadata", "--format",
                 "{{playerInstance}}|{{status}}|{{xesam:title}}|{{xesam:artist}}"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
            p_pulse = subprocess.Popen(
                ["pactl", "subscribe"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
            fds = [p_mpris.stdout, p_pulse.stdout]
            while not self.stop_ev.is_set():
                r, _, _ = select.select(fds, [], [], 2.0)
                if not r:
                    self.refresh_track()
                    continue
                dead = False
                relevant = False
                for f in r:
                    line = f.readline()
                    if not line:
                        dead = True
                    elif f == p_mpris.stdout or "sink-input" in line:
                        relevant = True
                if relevant:
                    time.sleep(0.08)
                    self.refresh_track()
                if dead:
                    break
            for p in (p_mpris, p_pulse):
                p.terminate()
                try:
                    p.wait(timeout=1)
                except Exception:
                    p.kill()
            time.sleep(0.5)

    def format_frame(self, vals):
        with self.lock:
            playing = self.playing
            label = self.track_label
            tooltip = self.track_tooltip
            elapsed = time.monotonic() - self.announce_start

        has_audio = any(v > 0 for v in vals)
        if not playing and not has_audio:
            return {"text": "", "tooltip": "Nada tocando", "class": "idle"}

        bars_str = "".join(CHARS[max(0, min(8, v))] for v in vals)
        if not bars_str.strip():
            bars_str = "▁" * BARS

        if label and 0.0 <= elapsed < ANNOUNCE_SEC:
            max_chars = 36
            shown_full = label if len(label) <= max_chars else label[: max_chars - 1] + "…"
            if elapsed < EXPAND_SEC:
                frac = elapsed / EXPAND_SEC
                n = max(1, round(len(shown_full) * frac))
                piece = shown_full[:n]
            elif elapsed > (ANNOUNCE_SEC - COLLAPSE_SEC):
                frac = max(0.0, (ANNOUNCE_SEC - elapsed) / COLLAPSE_SEC)
                n = max(1, round(len(shown_full) * frac))
                piece = shown_full[:n]
            else:
                piece = shown_full
            text = f"󰎈 {html.escape(piece)}  {bars_str[:5]}"
            return {"text": text, "tooltip": tooltip, "class": ["playing", "track-change"]}

        return {"text": bars_str, "tooltip": tooltip or "Tocando agora", "class": "playing"}

    def run(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        threading.Thread(target=self.watch_media, daemon=True).start()

        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as tf:
            tf.write(CAVA_CFG)
            cfg_path = tf.name

        cava_proc = None
        last_out = None
        try:
            cava_proc = subprocess.Popen(
                ["/usr/bin/cava", "-p", cfg_path],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )

            def emit(obj):
                nonlocal last_out
                s = json.dumps(obj, ensure_ascii=False)
                if s != last_out:
                    last_out = s
                    print(s, flush=True)

            while not self.stop_ev.is_set():
                r, _, _ = select.select([cava_proc.stdout], [], [], 0.4)
                if not r:
                    emit(self.format_frame([0] * BARS))
                    continue
                line = cava_proc.stdout.readline()
                if not line:
                    break
                parts = [p for p in line.strip().split(";") if p != ""]
                vals = []
                for p in parts[:BARS]:
                    try:
                        vals.append(int(p))
                    except ValueError:
                        vals.append(0)
                if len(vals) < BARS:
                    vals.extend([0] * (BARS - len(vals)))
                emit(self.format_frame(vals))
        finally:
            self.stop_ev.set()
            if cava_proc and cava_proc.poll() is None:
                cava_proc.terminate()
            try:
                os.unlink(cfg_path)
            except OSError:
                pass


if __name__ == "__main__":
    MiniCava().run()
