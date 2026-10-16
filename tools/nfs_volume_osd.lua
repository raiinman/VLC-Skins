-- Private VLC 3.0.x interface; only its owning VLC process is observed.
-- volume.get() returns AOUT_VOLUME_DEFAULT=256 at 100% (VLC 3.0.23
-- modules/lua/libs/volume.c and include/vlc_aout.h). The requested native
-- vertical bar is shown in windowed video too; hotkeys normally gate that
-- slider to fullscreen. Core vout_OSDSlider supports either video mode.
local CHANNEL_VAR = "nfs-volume-osd-slider-v1"
local POLL_US = 50000
local last_volume = nil

local function finite(value)
    return type(value) == "number" and value == value
        and value > -math.huge and value < math.huge
end

local function valid_channel(value)
    -- vlc.var.create(number) uses VLC_VAR_FLOAT: integers up to 2^24-1
    -- are exact. Never use an invalid or unrelated existing variable.
    -- vlc_vout.h reserves 0..7; registered channels start at 8.
    return finite(value) and value >= 8 and value <= 16777215
        and value == math.floor(value)
end

local function slider_channel(vout)
    local channel = vlc.var.get(vout, CHANNEL_VAR)
    if channel ~= nil then
        return valid_channel(channel) and channel or nil
    end
    channel = vlc.osd.channel_register()
    if not valid_channel(channel) then return nil end
    local status = vlc.var.create(vout, CHANNEL_VAR, channel)
    if status ~= 0 then return nil end
    return channel
end

local function show_volume(raw_volume)
    local percent = math.floor(raw_volume * 100 / 256 + 0.5)
    if not finite(percent) then return end
    local vout = vlc.object.vout()
    if vout == nil then return end
    -- Use the native default text channel, not the slider channel: native
    -- ephemeral subpictures on the same channel can replace each other.
    vlc.osd.message("Volume " .. tostring(percent) .. "%", nil,
        "top-right", 1200000)
    local channel = slider_channel(vout)
    if channel ~= nil then
        vlc.osd.slider(math.min(100, percent), "vertical", channel)
    end
end

while true do
    local ok, volume = pcall(vlc.volume.get)
    if ok and finite(volume) and volume >= 0 then
        if last_volume ~= nil and volume ~= last_volume then
            -- Input/vout can disappear between observation and display.
            -- OSD failures must never change playback or stop the monitor.
            pcall(show_volume, volume)
        end
        last_volume = volume
    end
    -- VLC interrupts this wait when the interface closes; let that error
    -- leave the loop rather than swallowing shutdown and spinning.
    vlc.misc.mwait(vlc.misc.mdate() + POLL_US)
end
