using System;
using System.Collections.Generic;
using System.Collections;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

static partial class Native
{
    internal const long Child=0x40000000L, Popup=0x80000000L, Caption=0x00C00000L, ThickFrame=0x00040000L;
    [StructLayout(LayoutKind.Sequential)] internal struct RECT { internal int Left, Top, Right, Bottom; }
    [DllImport("user32.dll", SetLastError=true)] internal static extern IntPtr SetParent(IntPtr child, IntPtr parent);
    [DllImport("user32.dll")] internal static extern IntPtr GetParent(IntPtr window);
    [DllImport("user32.dll", EntryPoint="GetWindowLongPtrW", SetLastError=true)] internal static extern IntPtr GetWindowLongPtr(IntPtr window, int index);
    [DllImport("user32.dll", EntryPoint="SetWindowLongPtrW", SetLastError=true)] static extern IntPtr SetWindowLongPtr(IntPtr window, int index, IntPtr value);
    [DllImport("kernel32.dll")] static extern void SetLastError(uint error);
    [DllImport("user32.dll")] internal static extern bool GetClientRect(IntPtr window, out RECT rect);
    [DllImport("user32.dll")] internal static extern bool GetWindowRect(IntPtr window, out RECT rect);
    [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr window);
    [DllImport("user32.dll")] internal static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll",EntryPoint="SetWindowTextW",CharSet=CharSet.Unicode)] internal static extern bool SetWindowText(IntPtr window,string text);
    delegate bool EnumWindowCallback(IntPtr window,IntPtr parameter);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowCallback callback,IntPtr parameter);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr window,StringBuilder name,int size);
    internal static IntPtr FindSizedWindow(int process,int width,int height)
    {
        IntPtr found=IntPtr.Zero,hidden=IntPtr.Zero;
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT area;
            if(OwnedBy(window,process) && GetWindowRect(window,out area) && area.Right-area.Left==width && area.Bottom-area.Top==height)
            {
                // Stock VLC's hidden fullscreen controller shares the main pane size.
                if(IsWindowVisible(window)) {found=window;return false;}
                if(hidden==IntPtr.Zero) hidden=window;
            }
            return true;
        },IntPtr.Zero);
        return found!=IntPtr.Zero ? found : hidden;
    }
    internal static IntPtr FindHudSignal(int process,out int width)
    {
        IntPtr found=IntPtr.Zero;int count=0,observed=0;
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT area;
            if(OwnedBy(window,process) && IsWindowVisible(window) && GetWindowRect(window,out area) &&
               area.Left==-31000 && area.Top==-30600 && area.Bottom-area.Top==17 &&
               area.Right-area.Left>=211 && area.Right-area.Left<=213)
            {count++;found=window;observed=area.Right-area.Left;}
            return true;
        },IntPtr.Zero);
        width=observed;return count==1 ? found : IntPtr.Zero;
    }
    internal static IntPtr FindPlaylistClearSignal(int process,out int width)
    {return FindClearWindow(process,-30100,17,161,162,true,out width);}
    internal static IntPtr FindStartupCommand(int process)
    {int width;return FindClearWindow(process,-29600,17,231,231,true,out width);}
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr GetProp(IntPtr window,string name);
    internal static bool StartupReady(int process)
    {return StartupIntro(process,false);}
    internal static bool StartupTriggered(int process)
    {return StartupIntro(process,true);}
    static bool StartupIntro(int process,bool triggered)
    {
        int count=0;
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT bounds;
            if(OwnedBy(window,process) && IsWindowVisible(window) && GetWindowRect(window,out bounds) &&
               bounds.Left==-31000 && bounds.Top==-31000 && bounds.Bottom-bounds.Top==17 &&
               (bounds.Right-bounds.Left==53 || (!triggered && bounds.Right-bounds.Left==43)) &&
               GetProp(window,"NfsSkinEffects.IntroReady")==new IntPtr(1)) count++;
            return true;
        },IntPtr.Zero);
        return count==1;
    }
    internal static bool? PlaylistClearCapability(int process)
    {
        int width;
        return FindClearWindow(process,-30000,1,171,172,false,out width)==IntPtr.Zero ? (bool?)null : width==172;
    }
    static IntPtr FindClearWindow(int process,int y,int height,int first,int last,bool visible,out int width)
    {
        IntPtr found=IntPtr.Zero;int count=0,observed=0;
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT area;
            if(OwnedBy(window,process) && (!visible || IsWindowVisible(window)) && GetWindowRect(window,out area) &&
               area.Left==-31000 && area.Top==y && area.Bottom-area.Top==height &&
               area.Right-area.Left>=first && area.Right-area.Left<=last)
            {count++;found=window;observed=area.Right-area.Left;}
            return true;
        },IntPtr.Zero);
        width=observed;return count==1 ? found : IntPtr.Zero;
    }
    [StructLayout(LayoutKind.Sequential)] struct GUI_THREAD_INFO
    {
        internal uint Size,Flags;
        internal IntPtr Active,Focus,Capture,MenuOwner,MoveSize,Caret;
        internal RECT CaretBounds;
    }
    [DllImport("user32.dll")] static extern bool GetGUIThreadInfo(uint thread,ref GUI_THREAD_INFO info);
    internal static bool TargetHasCapture(IntPtr window)
    {
        uint process;uint thread=GetWindowThreadProcessId(window,out process);
        var info=new GUI_THREAD_INFO {Size=(uint)Marshal.SizeOf(typeof(GUI_THREAD_INFO))};
        return thread==0 || !GetGUIThreadInfo(thread,ref info) || info.Capture!=IntPtr.Zero;
    }
    [StructLayout(LayoutKind.Sequential)] struct CURSOR_POINT {internal int X,Y;}
    [DllImport("user32.dll")] static extern bool GetCursorPos(out CURSOR_POINT point);
    [DllImport("user32.dll")] static extern IntPtr WindowFromPoint(CURSOR_POINT point);
    [DllImport("user32.dll")] static extern IntPtr GetAncestor(IntPtr window,uint flags);
    internal static bool HudSettingsBounds(int process,out Rectangle anchor)
    {IntPtr owner;return HudSettingsBounds(process,out anchor,out owner);}
    internal static bool HudSettingsBounds(int process,out Rectangle anchor,out IntPtr owner)
    {
        var candidates=new List<IntPtr>();
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT area;
            if(OwnedBy(window,process) && IsWindowVisible(window) && GetWindowRect(window,out area) &&
               area.Bottom-area.Top==64 && (area.Right-area.Left==360 || area.Right-area.Left==361)) candidates.Add(window);
            return true;
        },IntPtr.Zero);
        CURSOR_POINT cursor;IntPtr root=GetCursorPos(out cursor) ? GetAncestor(WindowFromPoint(cursor),2) : IntPtr.Zero;
        IntPtr selected=candidates.Contains(root) ? root : candidates.Count==1 ? candidates[0] : IntPtr.Zero;
        RECT bounds;anchor=Rectangle.Empty;owner=IntPtr.Zero;
        if(selected==IntPtr.Zero || !GetWindowRect(selected,out bounds)) return false;
        anchor=Rectangle.FromLTRB(bounds.Left,bounds.Top,bounds.Right,bounds.Bottom);owner=selected;return true;
    }
    internal static string WindowSizes(int process)
    {
        var sizes=new List<string>();
        EnumWindows(delegate(IntPtr window,IntPtr parameter) {
            RECT area;
            if(OwnedBy(window,process) && GetWindowRect(window,out area))
            {
                var name=new StringBuilder(128); GetClassName(window,name,name.Capacity);
                sizes.Add(name+" "+(area.Right-area.Left)+"x"+(area.Bottom-area.Top)+" at="+area.Left+","+area.Top+" visible="+IsWindowVisible(window));
            }
            return true;
        },IntPtr.Zero);
        return String.Join(", ",sizes);
    }
    [DllImport("user32.dll")] internal static extern bool ShowWindow(IntPtr window, int command);
    [DllImport("user32.dll")] internal static extern bool SetForegroundWindow(IntPtr window);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    internal static IntPtr PlaylistDialogWindow(int process,IntPtr fallback)
    {
        IntPtr active=GetForegroundWindow();
        return OwnedBy(active,process) ? active : OwnedBy(fallback,process) ? fallback : IntPtr.Zero;
    }
    [DllImport("user32.dll")] static extern IntPtr GetFocus();
    [DllImport("user32.dll")] static extern IntPtr SetFocus(IntPtr window);
    [DllImport("user32.dll")] static extern bool IsChild(IntPtr parent,IntPtr child);
    internal delegate void WinEventCallback(IntPtr hook,uint eventType,IntPtr window,int objectId,int childId,uint thread,uint time);
    [DllImport("user32.dll",SetLastError=true)] static extern IntPtr SetWinEventHook(uint first,uint last,IntPtr module,WinEventCallback callback,uint process,uint thread,uint flags);
    [DllImport("user32.dll")] internal static extern bool UnhookWinEvent(IntPtr hook);
    internal static IntPtr WatchProcessFocus(uint process,WinEventCallback callback) { return SetWinEventHook(0x8005,0x8005,IntPtr.Zero,callback,process,0,0); }
    internal static bool PaneFocusEvent(uint eventType,IntPtr window,IntPtr pane) { return eventType==0x8005 && pane!=IntPtr.Zero && window==pane; }
    internal static bool FocusedWindowIs(IntPtr window) { return window!=IntPtr.Zero && GetFocus()==window; }
    internal static bool Within(IntPtr parent,IntPtr child) { return parent!=IntPtr.Zero && child!=IntPtr.Zero && (parent==child || IsChild(parent,child)); }
    [DllImport("user32.dll", SetLastError=true)] internal static extern bool SetWindowPos(IntPtr window, IntPtr after, int x, int y, int width, int height, uint flags);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
    internal static bool OwnedBy(IntPtr window, int process) { uint actual; GetWindowThreadProcessId(window, out actual); return actual == process; }
    [DllImport("user32.dll",SetLastError=true)] static extern bool PostMessage(IntPtr window,uint message,UIntPtr wParam,IntPtr lParam);
    internal static void InvokeSkinOpen(IntPtr window,int process,int x,int y)
    {
        if(!IsWindow(window) || !OwnedBy(window,process)) throw new Exception("Skin command ownership check failed.");
        // Dispatch to our private VLC skin control so VLC updates its own visibility variable.
        // Showing the HWND directly would desynchronize the checkbox and close action.
        // Image.action2 needs no mouse-down. Capture-sensitive protocols defer
        // and use the matched DLL guard because VLC releases capture on dispatch.
        if(!PostMessage(window,0x203,UIntPtr.Zero,new IntPtr((x & 0xffff) | ((y & 0xffff)<<16))))
            throw new Win32Exception(Marshal.GetLastWin32Error(),"Could not queue the YouTube pane command.");
    }
    internal static void ParentChecked(IntPtr child, IntPtr parent)
    {
        SetLastError(0); IntPtr previous = SetParent(child,parent); int error = Marshal.GetLastWin32Error();
        if ((previous == IntPtr.Zero && error != 0) || GetParent(child) != parent) throw new Win32Exception(error, "Windows could not reparent the test window (expected=" + parent + ", actual=" + GetParent(child) + ", error=" + error + ").");
    }
    internal static void SetStyle(IntPtr window, int index, long style)
    {
        SetLastError(0); IntPtr previous = SetWindowLongPtr(window,index,new IntPtr(style)); int error=Marshal.GetLastWin32Error();
        if (previous == IntPtr.Zero && error != 0) throw new Win32Exception(error);
    }
}
