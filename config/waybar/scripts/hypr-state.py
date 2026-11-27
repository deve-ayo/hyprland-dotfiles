#!/usr/bin/env python3
"""Estado do Hyprland para a waybar (áreas de trabalho e app em foco).

O módulo hyprland/workspaces do Waybar 0.15 manda `dispatch workspace N` no clique,
sintaxe que o Hyprland em modo Lua rejeita (Alexays/Waybar#5008). Por isso as áreas
de trabalho são módulos custom/wsN que chamam `hl.dsp.focus()` no clique.

Este daemon escuta os eventos do Hyprland e grava um JSON por módulo em
$XDG_RUNTIME_DIR/waybar-hypr/<monitor>/ (ws1..wsN e window). Os módulos só leem
o arquivo quando recebem o sinal SIGRTMIN+8. Arquivo ausente = módulo escondido.
"""
import fcntl
import html
import json
import os
import select
import signal
import socket
import time
from pathlib import Path

SIGNAL = signal.SIGRTMIN + 8
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
OUT_DIR = RUNTIME / "waybar-hypr"
HYPR_DIR = RUNTIME / "hypr" / os.environ["HYPRLAND_INSTANCE_SIGNATURE"]

# Eventos (formato v1 e v2) que mudam algo que a barra mostra. Títulos de janela
# ficam de fora de propósito para evitar rajadas contínuas de sinalização.
EVENTS = {
    "workspace", "workspacev2",
    "createworkspace", "createworkspacev2",
    "destroyworkspace", "destroyworkspacev2",
    "moveworkspace", "moveworkspacev2",
    "renameworkspace",
    "focusedmon", "focusedmonv2",
    "monitoradded", "monitoraddedv2",
    "monitorremoved", "monitorremovedv2",
    "openwindow", "closewindow",
    "movewindow", "movewindowv2",
}

# Janelas que pediram atenção (evento urgent) e cuja área ainda não foi aberta.
URGENT = set()


def query(cmd):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(2.0)
        s.connect(str(HYPR_DIR / ".socket.sock"))
        s.sendall(f"j/{cmd}".encode())
        data = b""
        while chunk := s.recv(65536):
            data += chunk
    if not data:
        return None
    return json.loads(data)


def desktop_names():
    """classe da janela (minúscula) -> nome do app, lido dos arquivos .desktop."""
    dirs = [os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))]
    dirs += os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    by_wmclass, by_file = {}, {}
    for d in reversed(dirs):  # diretórios do usuário por último = prioridade
        for f in Path(d, "applications").glob("*.desktop"):
            fields, in_entry = {}, False
            try:
                for line in f.read_text(errors="ignore").splitlines():
                    if line.startswith("["):
                        in_entry = line.strip() == "[Desktop Entry]"
                    elif in_entry and "=" in line:
                        k, v = line.split("=", 1)
                        fields.setdefault(k.strip(), v.strip())
            except OSError:
                continue
            name = fields.get("Name[pt_BR]") or fields.get("Name[pt]") or fields.get("Name")
            if not name:
                continue
            if wm := fields.get("StartupWMClass"):
                by_wmclass[wm.lower()] = name
            by_file[f.stem.lower()] = name
            by_file.setdefault(f.stem.rsplit(".", 1)[-1].lower(), name)
    return {**by_file, **by_wmclass}


NAMES = desktop_names()


def app_name(client):
    cls = client.get("class") or client.get("initialClass") or ""
    if not cls:
        return client.get("title") or "?"
    return NAMES.get(cls.lower()) or cls[:1].upper() + cls[1:]


def build():
    """Monta {caminho relativo: conteúdo} para todos os módulos."""
    raw_ws = query("workspaces")
    raw_mon = query("monitors")
    raw_cli = query("clients")
    if not isinstance(raw_ws, list) or not isinstance(raw_mon, list) or not isinstance(raw_cli, list):
        return None

    workspaces = [
        w for w in raw_ws
        if isinstance(w, dict) and isinstance(w.get("id"), int) and w["id"] > 0
    ]
    monitors = [
        m for m in raw_mon
        if isinstance(m, dict) and isinstance(m.get("activeWorkspace"), dict) and m.get("name")
    ]
    clients = [
        c for c in raw_cli
        if isinstance(c, dict)
        and c.get("mapped", True)
        and isinstance(c.get("workspace"), dict)
        and isinstance(c["workspace"].get("id"), int)
    ]

    focused_mon = next((m for m in monitors if m.get("focused")), None)
    focused_ws = focused_mon["activeWorkspace"].get("id") if focused_mon else None
    visible = {m["activeWorkspace"].get("id") for m in monitors}
    ws_of = {c["address"]: c["workspace"]["id"] for c in clients if c.get("address")}
    # Esquece janelas fechadas e as da área que está aberta agora.
    URGENT.intersection_update(a for a, ws in ws_of.items() if ws != focused_ws)
    urgent_ws = {ws_of[a] for a in URGENT if a in ws_of}

    files, tooltips = {}, {}
    for w in workspaces:
        ws_id = w["id"]
        apps = {}
        for c in sorted(clients, key=lambda c: c.get("focusHistoryID", 9999)):
            if c["workspace"]["id"] == ws_id:
                name = app_name(c)
                apps[name] = apps.get(name, 0) + 1
        lines = [f"<b>Área de trabalho {ws_id}</b>"]
        lines += [f"• {html.escape(n)}" + (f"  ×{k}" if k > 1 else "") for n, k in apps.items()]
        if not apps:
            lines.append("<i>vazia</i>")
        tooltips[ws_id] = "\n".join(lines)
        classes = ["ws"]
        if ws_id == focused_ws:
            classes.append("active")
        if ws_id in visible:
            classes.append("visible")
        if not apps:
            classes.append("empty")
        if ws_id in urgent_ws:
            text = f"{ws_id} !"
            classes.append("urgent")
        else:
            text = str(ws_id)
        data = json.dumps({"text": text, "tooltip": tooltips[ws_id], "class": classes})
        mon_name = w.get("monitor")
        if mon_name:
            files[f"{mon_name}/ws{ws_id}"] = data
        files[f"_all/ws{ws_id}"] = data

    # App em foco: por monitor, a última janela focada na área visível dele.
    targets = list(monitors)
    if focused_mon:
        targets.append({**focused_mon, "name": "_all"})
    for m in targets:
        ws_id = m["activeWorkspace"].get("id")
        here = [c for c in clients if c["workspace"]["id"] == ws_id]
        if not here:
            files[f"{m['name']}/window"] = json.dumps({
                "text": "Área de trabalho",
                "tooltip": "Área de trabalho vazia",
                "class": "window",
            })
            continue
        c = min(here, key=lambda c: c.get("focusHistoryID", 9999))
        files[f"{m['name']}/window"] = json.dumps({
            "text": html.escape(app_name(c)),
            "tooltip": html.escape(c.get("title") or app_name(c)),
            "class": "window",
        })
    return files


def sync(files, current):
    """Grava só o que mudou; devolve True se algo mudou."""
    changed = False
    for rel in current.keys() - files.keys():
        (OUT_DIR / rel).unlink(missing_ok=True)
        changed = True
    for rel, data in files.items():
        if current.get(rel) == data:
            continue
        path = OUT_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(data + "\n")
        tmp.replace(path)
        changed = True
    return changed


def signal_waybar():
    for proc in Path("/proc").iterdir():
        if proc.name.isdigit():
            try:
                if (proc / "comm").read_text().strip() == "waybar":
                    os.kill(int(proc.name), SIGNAL)
            except OSError:
                pass


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Uma instância só, mesmo com a barra aberta em vários monitores; as outras
    # esperam na trava e assumem se esta morrer.
    lock = open(OUT_DIR / ".lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)

    current = {}
    for f in OUT_DIR.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            f.unlink()

    while True:
        events = None
        try:
            events = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            events.connect(str(HYPR_DIR / ".socket2.sock"))
            buf, focused = b"", None
            while True:
                files = build()
                if files is not None and sync(files, current):
                    signal_waybar()
                    current = files

                # Espera um evento relevante e junta a rajada que vem logo em seguida.
                relevant, timeout = False, 5.0
                while True:
                    ready, _, _ = select.select([events], [], [], timeout)
                    if not ready:
                        break
                    chunk = events.recv(65536)
                    if not chunk:
                        raise ConnectionResetError("socket2 EOF")
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    for line in lines:
                        name, _, data = line.decode(errors="ignore").partition(">>")
                        if name == "activewindowv2":
                            if data != focused:
                                focused, relevant = data, True
                        elif name == "urgent":
                            URGENT.add("0x" + data.removeprefix("0x"))
                            relevant = True
                        elif name in EVENTS:
                            relevant = True
                    if relevant:
                        timeout = 0.03
        except Exception:
            time.sleep(0.5)
        finally:
            if events is not None:
                try:
                    events.close()
                except OSError:
                    pass


if __name__ == "__main__":
    main()
