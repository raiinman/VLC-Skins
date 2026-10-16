/* Correct queued wheel coordinates and protect capture from clock commands.
 * The helper installs this DLL on one validated VLC UI thread, never globally.
 * No input generation, cursor/focus changes, logging, files or media APIs.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <windowsx.h>
#include <limits.h>

#define PROP_ENABLED L"NfsSkinWheelBridge.Enabled"
#define PROP_OWNER L"NfsSkinWheelBridge.OwnerPid"
#define PROP_X L"NfsSkinWheelBridge.OriginX"
#define PROP_Y L"NfsSkinWheelBridge.OriginY"
#define ENABLED_MARKER ((ULONG_PTR)0x4E465357)

__declspec(dllexport) LRESULT CALLBACK CorrectWheel(int code, WPARAM removed, LPARAM payload)
{
    if (code == HC_ACTION && removed == PM_REMOVE && payload != 0)
    {
        MSG *message = (MSG *)payload;
        /* VLC releases native capture unconditionally for a double-click.
         * Suppress only the exact offscreen clock/playlist protocols while this GUI
         * thread owns capture. This runs after dequeue, closing the race
         * between the helper's pre-post check and VLC's event dispatch.
         */
        if (message->message == WM_LBUTTONDBLCLK && message->hwnd != NULL && GetCapture() != NULL)
        {
            DWORD pid = 0;
            DWORD thread = GetWindowThreadProcessId(message->hwnd, &pid);
            WCHAR name[32];
            RECT bounds;
            if (pid == GetCurrentProcessId() && thread == GetCurrentThreadId() &&
                GetClassNameW(message->hwnd, name, 32) == 15 && lstrcmpW(name, L"SkinWindowClass") == 0 &&
                GetWindowRect(message->hwnd, &bounds) && bounds.left == -31000 && bounds.bottom - bounds.top == 17)
            {
                LONG width = bounds.right - bounds.left;
                BOOL clock_command = bounds.top == -30200 && width >= 151 && width <= 154;
                int x = GET_X_LPARAM(message->lParam), y = GET_Y_LPARAM(message->lParam);
                BOOL playlist_command = bounds.top == -30100 && (width == 161 || width == 162) &&
                    y == 0 && (x == 0 || x == 10 || x == 20);
                BOOL fixed_clock_command = bounds.top == -29900 && width == 181 &&
                    y == 0 && (x == 0 || x == 10);
                BOOL snapping_command = bounds.top == -29800 && (width == 191 || width == 192) &&
                    y == 0 && (x == 0 || x == 10 || x == 20 || x == 30);
                BOOL startup_command = bounds.top == -29600 && width == 231 &&
                    y >= 0 && y < 3 && ((x >= 0 && x < 3) || (x >= 10 && x < 13));
                if (clock_command || playlist_command || fixed_clock_command || snapping_command || startup_command)
                    message->message = WM_NULL;
            }
        }
        if (message->message == WM_MOUSEWHEEL && message->hwnd != NULL &&
            (ULONG_PTR)GetPropW(message->hwnd, PROP_ENABLED) == ENABLED_MARKER)
        {
            HWND window = message->hwnd;
            DWORD pid = 0;
            DWORD thread = GetWindowThreadProcessId(window, &pid);
            WCHAR name[32];
            RECT bounds;
            LONG_PTR origin_x = (LONG_PTR)GetPropW(window, PROP_X);
            LONG_PTR origin_y = (LONG_PTR)GetPropW(window, PROP_Y);
            /* These are canonical physical positions at both artwork scales.
             * Refuse saved/custom origins rather than guess VLC's internal state.
             */
            if (pid == GetCurrentProcessId() && thread == GetCurrentThreadId() &&
                (ULONG_PTR)GetPropW(window, PROP_OWNER) == (ULONG_PTR)pid &&
                origin_x == -31000 && origin_y == -30800 &&
                IsWindowVisible(window) && !IsIconic(window) &&
                GetClassNameW(window, name, 32) == 15 && lstrcmpW(name, L"SkinWindowClass") == 0 &&
                GetWindowRect(window, &bounds) && bounds.right - bounds.left == 361 && bounds.bottom - bounds.top == 64)
            {
                POINT point = { GET_X_LPARAM(message->lParam), GET_Y_LPARAM(message->lParam) };
                if (PtInRect(&bounds, point))
                {
                    LONG_PTR x = origin_x + point.x - bounds.left;
                    LONG_PTR y = origin_y + point.y - bounds.top;
                    if (x >= SHRT_MIN && x <= SHRT_MAX && y >= SHRT_MIN && y <= SHRT_MAX)
                        message->lParam = MAKELPARAM((WORD)(SHORT)x, (WORD)(SHORT)y);
                }
            }
        }
    }
    return CallNextHookEx(NULL, code, removed, payload);
}
