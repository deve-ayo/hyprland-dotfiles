-- Hyprland configuration (Lua API hl.*)
-- Reference: https://wiki.hypr.land

local HOME = os.getenv("HOME") or ""

------------------
---- MONITORS ----
------------------
hl.monitor({ output = "eDP-1", mode = "preferred", position = "0x0", scale = 1, transform = 0, disabled = false, mirror = "" })
hl.monitor({ output = "HDMI-A-2", mode = "preferred", position = "1920x0", scale = 1, transform = 0, disabled = false, mirror = "" })

---------------------
---- MY PROGRAMS ----
---------------------
local terminal    = "kitty"
local fileManager = "nautilus"
local menu        = "wofi --show drun"
local browser     = "firefox"

-------------------
---- AUTOSTART ----
-------------------
hl.on("hyprland.start", function ()
    hl.exec_cmd("awww-daemon")
end)

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("QT_STYLE_OVERRIDE", "kvantum")
hl.env("XCURSOR_THEME", "Bibata-Modern-Classic")

-----------------------
---- LOOK AND FEEL ----
-----------------------
hl.config({
    general = {
        gaps_in  = 5,
        gaps_out = 10,

        border_size = 2,

        col = {
            active_border   = "rgba(82c4f8d9)",
            inactive_border = "rgba(8a95a233)",
        },

        resize_on_border = true,
        allow_tearing = false,
        layout = "dwindle",
    },

    decoration = {
        rounding       = 14,
        rounding_power = 2,

        active_opacity   = 1,
        inactive_opacity = 1,

        dim_inactive     = true,
        dim_strength     = 0.06,

        shadow = {
            enabled      = true,
            range        = 22,
            render_power = 3,
            color        = 0x66000000,
        },

        blur = {
            enabled   = true,
            size      = 6,
            passes    = 2,
            vibrancy  = 0.22,
        },
    },

    animations = {
        enabled = true,
    },
})

-- Cores das bordas geradas pelo wallust a partir do papel de parede
pcall(dofile, HOME .. "/.cache/wallust/hyprland.lua")

hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}    } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1}    } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}       } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1}    } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}     } })
hl.curve("smoothOut",      { type = "bezier", points = { {0.16, 1},    {0.3, 1}     } })
hl.curve("smoothClose",    { type = "bezier", points = { {0.25, 0.1},  {0.25, 1}    } })

hl.curve("easy",           { type = "spring", mass = 1, stiffness = 238.1191, dampening = 24.21279333 })

hl.animation({ leaf = "global",        enabled = true,  speed = 10,   bezier = "default" })
hl.animation({ leaf = "border",        enabled = true,  speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows",       enabled = true,  speed = 4.79, spring = "easy" })
hl.animation({ leaf = "windowsIn",     enabled = true,  speed = 4.1,  spring = "easy",         style = "popin 87%" })
hl.animation({ leaf = "windowsOut",    enabled = true,  speed = 1.49, bezier = "linear",       style = "popin 87%" })
hl.animation({ leaf = "fadeIn",        enabled = true,  speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut",       enabled = true,  speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade",          enabled = true,  speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "fadeSwitch",    enabled = true,  speed = 3.5,  bezier = "easeOutQuint" })
hl.animation({ leaf = "fadeDim",       enabled = true,  speed = 3.5,  bezier = "easeOutQuint" })
hl.animation({ leaf = "layers",        enabled = true,  speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn",      enabled = true,  speed = 3.4,  bezier = "smoothOut",   style = "fade" })
hl.animation({ leaf = "layersOut",     enabled = true,  speed = 2.8,  bezier = "smoothClose", style = "fade" })
hl.animation({ leaf = "fadeLayersIn",  enabled = true,  speed = 3.0,  bezier = "smoothOut" })
hl.animation({ leaf = "fadeLayersOut", enabled = true,  speed = 2.6,  bezier = "smoothClose" })
hl.animation({ leaf = "workspaces",    enabled = true,  speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesIn",  enabled = true,  speed = 1.21, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesOut", enabled = true,  speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "zoomFactor",    enabled = true,  speed = 7,    bezier = "quick" })

hl.config({
    dwindle = {
        preserve_split = true,
    },
})

hl.config({
    master = {
        new_status = "master",
    },
})

hl.config({
    scrolling = {
        fullscreen_on_one_column = true,
    },
})

----------------
----  MISC  ----
----------------
hl.config({
    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo   = false,
    },
})

---------------
---- INPUT ----
---------------
hl.config({
    input = {
        kb_layout  = "us,br",
        kb_variant = ",abnt2",
        kb_model   = "",
        kb_options = "grp:alt_shift_toggle",
        kb_rules   = "",

        follow_mouse = 1,

        sensitivity = 0.15,
        accel_profile = "flat",

        touchpad = {
            natural_scroll = false,
        },
    },
})

pcall(dofile, HOME .. "/.config/hypr/input-desk.lua")

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace"
})

---------------------
---- KEYBINDINGS ----
---------------------
local mainMod = "SUPER"

hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd(terminal))
local closeWindowBind = hl.bind(mainMod .. " + C", hl.dsp.window.close())
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))

-- Tela cheia / maximizar mantendo a barra
hl.bind(mainMod .. " + Return",         hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind(mainMod .. " + SHIFT + Return", hl.dsp.window.fullscreen({ mode = "maximized",  action = "toggle" }))

-- Alterna entre telas espelhadas, estendidas e cada monitor individual.
hl.bind(mainMod .. " + F8", hl.dsp.exec_cmd("/usr/bin/python3 " .. HOME .. "/.config/hypr/scripts/alternar-telas.py"))

-- Luz noturna (SUPER + N)
local LUZ = HOME .. "/.config/hypr/scripts/luz-noturna.sh"
local luz = { modo = false, ajustou = false }

luz.vigia = hl.timer(function()
    if luz.modo and not (hl.is_key_down("Super_L") or hl.is_key_down("Super_R")) then
        luz.modo = false
        luz.vigia:set_enabled(false)
        if not luz.ajustou then hl.exec_cmd(LUZ .. " alternar") end
    end
end, { timeout = 40, type = "repeat" })
luz.vigia:set_enabled(false)

hl.bind(mainMod .. " + N", function()
    luz.modo, luz.ajustou = true, false
    luz.vigia:set_enabled(true)
end)

local function luz_ajustar(acao)
    luz.ajustou = true
    hl.exec_cmd(LUZ .. " " .. acao)
end

hl.bind(mainMod .. " + left", function()
    if luz.modo then luz_ajustar("menos")
    else hl.dispatch(hl.dsp.focus({ direction = "left" })) end
end)
hl.bind(mainMod .. " + right", function()
    if luz.modo then luz_ajustar("mais")
    else hl.dispatch(hl.dsp.focus({ direction = "right" })) end
end)
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

for _, dir in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(mainMod .. " + CTRL + " .. dir, hl.dsp.window.move({ direction = dir }))
    hl.bind(mainMod .. " + ALT + " .. dir,  hl.dsp.window.swap({ direction = dir }))
end

hl.bind(mainMod .. " + SHIFT + left",  hl.dsp.window.resize({ x = -40, y = 0,   relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.resize({ x = 40,  y = 0,   relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + up",    hl.dsp.window.resize({ x = 0,   y = -40, relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + down",  hl.dsp.window.resize({ x = 0,   y = 40,  relative = true }), { repeating = true })

for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key,         hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

local VOLUME = HOME .. "/.config/hypr/scripts/volume.sh"
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(VOLUME .. " raise"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(VOLUME .. " lower"), { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd(VOLUME .. " mute"),  { locked = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("swayosd-client --input-volume mute-toggle"), { locked = true })
hl.bind("XF86MonBrightnessUp",  hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })
hl.bind("F6",                    hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })
hl.bind("F7",                    hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })

hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })
hl.bind(mainMod .. " + F10", hl.dsp.exec_cmd("playerctl previous"),   { locked = true })
hl.bind(mainMod .. " + F11", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind(mainMod .. " + F12", hl.dsp.exec_cmd("playerctl next"),       { locked = true })

-------------------------------
------- APPS KEYBINDS ---------
-------------------------------
hl.bind(mainMod .. " + F",         hl.dsp.exec_cmd(browser))
hl.bind(mainMod .. " + O",         hl.dsp.exec_cmd("obsidian"))
hl.bind(mainMod .. " + ALT + C",   hl.dsp.exec_cmd("code"))
hl.bind(mainMod .. " + ALT + S",   hl.dsp.exec_cmd("spotify"))
hl.bind(mainMod .. " + L",         hl.dsp.exec_cmd("loginctl lock-session"), { locked = true })
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("cliphist list | wofi --dmenu --prompt 'Área de transferência' | cliphist decode | wl-copy"))

hl.bind(mainMod .. " + B",         hl.dsp.exec_cmd("killall -SIGUSR1 waybar"))
hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd("systemctl --user restart waybar.service"))
hl.bind(mainMod .. " + ALT + B",   hl.dsp.exec_cmd(HOME .. "/.config/hypr/scripts/toggle-bw.sh"), { locked = true })

-----------------------------
---- PAPEL DE PAREDE --------
-----------------------------
hl.bind(mainMod .. " + W",         hl.dsp.exec_cmd(HOME .. "/.config/hypr/scripts/wallpaper.sh --pick"))
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd(HOME .. "/.config/hypr/scripts/wallpaper.sh --random"))

-----------------------------
---- ATALHOS DE PRINT -------
-----------------------------
hl.bind("code:107",                hl.dsp.exec_cmd("hyprshot -m region -o " .. HOME .. "/Pictures/PrintScr"))
hl.bind(mainMod .. " + code:107",  hl.dsp.exec_cmd("hyprshot -m output -o " .. HOME .. "/Pictures/PrintScr"))

-------------------------------
---- CLAMSHELL (TAMPA) --------
-------------------------------
hl.bind("switch:on:Lid Switch",  hl.dsp.exec_cmd(HOME .. "/.config/hypr/scripts/lid.sh close"), { locked = true })
hl.bind("switch:off:Lid Switch", hl.dsp.exec_cmd(HOME .. "/.config/hypr/scripts/lid.sh open"),  { locked = true })

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------
hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },
    no_focus = true,
})

hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },
    move  = "20 monitor_h-120",
    float = true,
})

hl.window_rule({
    name    = "kitty-vidro",
    match   = { class = "kitty" },
    opacity = "0.92 0.85",
})

hl.window_rule({
    name    = "cava-opaco",
    match   = { class = "kitty", title = "^cava$" },
    opacity = "1.0 override 1.0 override",
})

hl.window_rule({
    name   = "portal-arquivos",
    match  = { class = "xdg-desktop-portal-gtk" },
    float  = true,
    size   = "1000 650",
    center = true,
})

hl.window_rule({
    name              = "firefox-pip",
    match             = { title = "^Picture-in-Picture$" },
    float             = true,
    pin               = true,
    keep_aspect_ratio = true,
    size              = "640 360",
    move              = "monitor_w-660 monitor_h-380",
})

hl.window_rule({
    name         = "tela-cheia-sem-descanso",
    match        = { class = ".*" },
    idle_inhibit = "fullscreen",
})

for _, ns in ipairs({ "top", "wofi", "swaync-control-center", "swaync-notification-window", "hyprshell" }) do
    hl.layer_rule({
        name         = "desfoque-" .. ns,
        match        = { namespace = "^" .. ns .. "$" },
        blur         = true,
        ignore_alpha = 0.3,
    })
end

hl.layer_rule({
    name      = "animacao-wofi",
    match     = { namespace = "^wofi$" },
    animation = "popin 88%",
})

hl.layer_rule({
    name    = "cava-fundo",
    match   = { namespace = "^cava-fundo$" },
    no_anim = true,
})

hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})
