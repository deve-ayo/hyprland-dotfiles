#!/usr/bin/env python3
"""Gera userChrome.css e userContent.css com a paleta Wallust em todos os perfis locais do Firefox e Zen Browser."""
import configparser
import json
import re
from pathlib import Path

home = Path.home()
palette_file = home / ".cache/wallust/pywal.json"
palette = json.loads(palette_file.read_text())
colors = palette.get("colors", {})
bg = palette["special"]["background"]
fg = palette["special"]["foreground"]
accent = colors.get("color4", "#3584e4")
surface = colors.get("color0", bg)
selected = colors.get("color8", accent)

css = f'''/* Gerado automaticamente a partir do papel de parede por tema-firefox.py. */
:root {{
  --toolbar-bgcolor: {bg} !important;
  --toolbar-color: {fg} !important;
  --lwt-accent-color: {bg} !important;
  --lwt-text-color: {fg} !important;
  --lwt-selected-tab-background-color: {bg} !important;
  --lwt-toolbarbutton-icon-fill: {fg} !important;
  --urlbar-box-bgcolor: {surface} !important;
  --urlbar-box-text-color: {fg} !important;
  --urlbar-box-focus-bgcolor: {surface} !important;
  --urlbar-box-focus-text-color: {fg} !important;
  --toolbar-field-background-color: {surface} !important;
  --toolbar-field-color: {fg} !important;
  --toolbar-field-focus-background-color: {surface} !important;
  --toolbar-field-focus-color: {fg} !important;
  --focus-outline-color: {accent} !important;
  --tab-selected-bgcolor: {bg} !important;
  /* Zen Browser */
  --zen-main-browser-background: {bg} !important;
  --zen-main-browser-background-toolbar: {bg} !important;
  --zen-themed-toolbar-bg: {bg} !important;
  --zen-themed-toolbar-bg-transparent: {bg} !important;
  --zen-colors-primary: {surface} !important;
  --zen-colors-secondary: {bg} !important;
  --zen-colors-tertiary: {bg} !important;
  --zen-colors-border: {selected} !important;
  --zen-primary-color: {accent} !important;
}}
#navigator-toolbox, #nav-bar, #TabsToolbar, #PersonalToolbar,
#sidebar-box, #sidebar-header, #zen-appcontent-navbar-wrapper,
#zen-sidebar-top-buttons, #zen-workspaces-button {{ background-color: {bg} !important; color: {fg} !important; }}
.tabbrowser-tab[selected] .tab-background {{ background-color: {bg} !important; box-shadow: inset 0 2px {accent} !important; }}
.tabbrowser-tab:hover .tab-background:not([selected]) {{ background-color: {surface} !important; }}
#urlbar-background, #searchbar {{ background-color: {surface} !important; border-color: {accent} !important; }}
'''

content_css = f'''/* Gerado automaticamente a partir do tema ativo por tema-firefox.py. */
@-moz-document url("about:home"), url("about:newtab"), url("about:blank") {{
  body, html {{ background-color: {bg} !important; color: {fg} !important; }}
  .search-wrapper .search-handoff-button, .search-inner-wrapper input {{
    background-color: {surface} !important; color: {fg} !important; border: 1px solid {accent} !important;
  }}
  .top-site-outer .tile {{ background-color: {surface} !important; }}
}}
'''

roots = (
    home / ".mozilla/firefox",
    home / ".config/mozilla/firefox",
    home / ".config/zen",
    home / ".zen",
)
pref = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'
for mozilla in roots:
    ini = mozilla / "profiles.ini"
    if not ini.exists():
        continue
    config = configparser.ConfigParser()
    config.read(ini)
    for section in config.sections():
        if not section.startswith("Profile"):
            continue
        relative = config.get(section, "Path", fallback=None)
        if not relative:
            continue
        path = Path(relative)
        if config.getboolean(section, "IsRelative", fallback=True):
            path = mozilla / path
        chrome = path / "chrome"
        chrome.mkdir(parents=True, exist_ok=True)
        (chrome / "userChrome.css").write_text(css)
        (chrome / "userContent.css").write_text(content_css)
        userjs = path / "user.js"
        contents = userjs.read_text() if userjs.exists() else ""
        contents = re.sub(r'(?m)^user_pref\("toolkit\.legacyUserProfileCustomizations\.stylesheets",.*\);\s*$', "", contents)
        userjs.write_text(contents.rstrip() + "\n" + pref + "\n")
        print(f"Tema Firefox atualizado: {path}")
