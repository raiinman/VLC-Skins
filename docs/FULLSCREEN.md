# Framed fullscreen

The controller fullscreen button and the video pane's original plus button now fill the current monitor while retaining the skin border. Click either again to restore the pane's previous size and position. The two-button video header and all original normal, hover and pressed assets remain intact; no third icon was added.

Double-click the video itself for VLC's native borderless fullscreen. Double-click again to leave it. No input overlay intercepts the video. These two modes are independent: leaving borderless fullscreen returns to the framed pane, including its maximized state if selected previously.

The buttons use `Checkbox state="video.isMaximized"`, `video.maximize()` and `video.unmaximize()`. The controller also shows the video window. Both Checkbox states reuse the same original feedback resources. Windows Skins2 maximize uses the nearest monitor's full rectangle, including the taskbar area. The video layout allows up to 8192x4320; frame geometry stays at the selected 1x/2x scale. Only video exposes maximize because VLC shares one saved restore rectangle among skin windows. Restore geometry lasts for the current session; it is not a persistent window history.

Offline checks cover source artwork, both toggle actions, packaged XML, frame/control clearance and monitor-size bounds. Native maximize/restore and video double-click have not been exercised on this build; this update does not launch VLC or take desktop input. Restart the companion or reload the updated standalone skin to use it.

Official VLC 3.0.23 sources: [action interpreter](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/interpreter.cpp), [maximize/restore](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/window_manager.cpp), [monitor bounds](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_factory.cpp), [video double-click](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/vout_window.cpp), [fullscreen toggle](https://github.com/videolan/vlc/blob/3.0.23/src/video_output/event.h). Context7 returned Lua/legacy examples; the implementation uses pinned official Skins2 source.
