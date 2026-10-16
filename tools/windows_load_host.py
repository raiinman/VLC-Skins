"""Owned benchmark processes on a desktop which is never switched to input."""
import ctypes as C
from ctypes import wintypes as W
import os
import socket
import subprocess
import uuid


class STARTUPINFO(C.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR),
                ('lpTitle', W.LPWSTR), ('dwX', W.DWORD), ('dwY', W.DWORD),
                ('dwXSize', W.DWORD), ('dwYSize', W.DWORD), ('dwXCountChars', W.DWORD),
                ('dwYCountChars', W.DWORD), ('dwFillAttribute', W.DWORD),
                ('dwFlags', W.DWORD), ('wShowWindow', W.WORD), ('cbReserved2', W.WORD),
                ('lpReserved2', C.POINTER(W.BYTE)), ('hStdInput', W.HANDLE),
                ('hStdOutput', W.HANDLE), ('hStdError', W.HANDLE)]


class PROCESSINFO(C.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE),
                ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


class MEMORY(C.Structure):
    _fields_ = [('cb', W.DWORD), ('PageFaultCount', W.DWORD)] + [
        (name, C.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


k = C.WinDLL('kernel32', use_last_error=True)
u = C.WinDLL('user32', use_last_error=True)
p = C.WinDLL('psapi', use_last_error=True)


def api(dll, name, restype, *argtypes):
    result = getattr(dll, name)
    result.restype, result.argtypes = restype, argtypes
    return result


create_desktop = api(u, 'CreateDesktopW', W.HANDLE, W.LPCWSTR, W.LPCWSTR, W.LPVOID, W.DWORD, W.DWORD, W.LPVOID)
close_desktop = api(u, 'CloseDesktop', W.BOOL, W.HANDLE)
open_input = api(u, 'OpenInputDesktop', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
object_info = api(u, 'GetUserObjectInformationW', W.BOOL, W.HANDLE, C.c_int, W.LPVOID, W.DWORD, C.POINTER(W.DWORD))
create_process = api(k, 'CreateProcessW', W.BOOL, W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID,
                     W.BOOL, W.DWORD, W.LPVOID, W.LPCWSTR, C.POINTER(STARTUPINFO), C.POINTER(PROCESSINFO))
close_handle = api(k, 'CloseHandle', W.BOOL, W.HANDLE)
wait = api(k, 'WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
exit_code = api(k, 'GetExitCodeProcess', W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
terminate = api(k, 'TerminateProcess', W.BOOL, W.HANDLE, W.UINT)
memory_info = api(p, 'GetProcessMemoryInfo', W.BOOL, W.HANDLE, C.POINTER(MEMORY), W.DWORD)
open_process = api(k, 'OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
process_times = api(k, 'GetProcessTimes', W.BOOL, W.HANDLE, C.POINTER(W.FILETIME),
                    C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME))
tcp_table = api(C.WinDLL('iphlpapi', use_last_error=True), 'GetExtendedTcpTable', W.DWORD,
                W.LPVOID, C.POINTER(W.DWORD), W.BOOL, W.ULONG, C.c_int, W.ULONG)


class TCPROW(C.Structure):
    _fields_ = [(name,W.DWORD) for name in ('state','local_address','local_port',
                                          'remote_address','remote_port','pid')]


def owns_tcp(pid, port, peer_port=None):
    # Validate an established server endpoint before writing any RC command;
    # unlike a port reservation, this remains bound to the connected process.
    for attempt in range(3):
        size=W.DWORD()
        status=tcp_table(None,C.byref(size),False,2,5,0)
        if status not in (0,122) or not 4<=size.value<=8*1024*1024:
            return False
        buffer=C.create_string_buffer(size.value)
        status=tcp_table(buffer,C.byref(size),False,2,5,0)
        if status==122:continue
        if status:return False
        count=C.cast(buffer,C.POINTER(W.DWORD)).contents.value
        if count>(size.value-4)//C.sizeof(TCPROW):return False
        rows=[TCPROW.from_buffer_copy(buffer,4+i*C.sizeof(TCPROW)) for i in range(count)]
        loopback=int.from_bytes(socket.inet_aton('127.0.0.1'),'little')
        candidates=[r for r in rows if socket.ntohs(r.local_port & 65535)==port and
                    r.local_address in (0,loopback) and
                    (peer_port is None and r.state==2 or peer_port is not None and
                     r.state==5 and r.remote_address==loopback and socket.ntohs(r.remote_port & 65535)==peer_port)]
        return len(candidates)==1 and candidates[0].pid==pid and candidates[0].local_address==loopback
    return False


def input_desktop():
    handle = open_input(0, False, 1)  # READOBJECTS only, no switch/input rights.
    if not handle:
        raise C.WinError(C.get_last_error())
    try:
        name, needed = C.create_unicode_buffer(256), W.DWORD()
        if not object_info(handle, 2, name, C.sizeof(name), C.byref(needed)):
            raise C.WinError(C.get_last_error())
        return name.value
    finally:
        close_desktop(handle)


class ProcessGuard:
    def __init__(self, pid):
        self.pid = pid
        self.handle = open_process(0x101000, False, pid)
        if not self.handle:
            raise C.WinError(C.get_last_error())
        values = [W.FILETIME() for _ in range(4)]
        if not process_times(self.handle, *(C.byref(value) for value in values)):
            self.close()
            raise C.WinError(C.get_last_error())
        self.started = (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime
        if not self.alive():
            self.close()
            raise RuntimeError('Protected process already exited')

    def alive(self):
        return wait(self.handle, 0) == 258

    def close(self):
        if self.handle:
            close_handle(self.handle)
            self.handle = None


class DesktopProcess:
    def __init__(self, args, env):
        self.args, self.handle, self.desktop = args, None, None
        name = 'NfsLoad_' + uuid.uuid4().hex
        # READOBJECTS|CREATEWINDOW|CREATEMENU|ENUMERATE|WRITEOBJECTS.
        # No SWITCHDESKTOP, hooks or journal/input privileges.
        self.desktop = create_desktop(name, None, None, 0, 0xC7, None)
        if not self.desktop:
            raise C.WinError(C.get_last_error())
        try:
            startup, info = STARTUPINFO(), PROCESSINFO()
            startup.cb = C.sizeof(startup)
            startup.lpDesktop = 'WinSta0\\' + name
            command = C.create_unicode_buffer(subprocess.list2cmdline(args))
            block = C.create_unicode_buffer('\0'.join(f'{key}={value}' for key, value in sorted(env.items(), key=lambda x:x[0].lower()))+'\0\0')
            if not create_process(args[0], command, None, None, False, 0x400, block,
                                  os.path.dirname(args[0]), C.byref(startup), C.byref(info)):
                raise C.WinError(C.get_last_error())
            self.handle, self.pid = info.hProcess, info.dwProcessId
            close_handle(info.hThread)
        except BaseException:
            close_desktop(self.desktop)
            self.desktop = None
            raise

    def poll(self):
        state = wait(self.handle, 0)
        if state == 258:
            return None
        if state != 0:
            raise C.WinError(C.get_last_error())
        value = W.DWORD()
        if not exit_code(self.handle, C.byref(value)):
            raise C.WinError(C.get_last_error())
        return value.value

    def wait(self, timeout):
        state = wait(self.handle, round(timeout*1000))
        if state == 258:
            raise subprocess.TimeoutExpired(self.args, timeout)
        return self.poll()

    def terminate(self):
        if self.poll() is None and not terminate(self.handle, 2):
            raise C.WinError(C.get_last_error())

    def memory(self):
        counters = MEMORY()
        counters.cb = C.sizeof(counters)
        if not memory_info(self.handle, C.byref(counters), C.sizeof(counters)):
            raise C.WinError(C.get_last_error())
        return {name:round(getattr(counters, name)/1024**2, 1)
                for name in ('WorkingSetSize', 'PeakWorkingSetSize', 'PrivateUsage')}

    def close(self):
        try:
            if self.handle:
                self.terminate()
                self.wait(10)
        finally:
            if self.handle:
                close_handle(self.handle)
                self.handle = None
            if self.desktop:
                success=close_desktop(self.desktop)
                self.desktop = None
                if not success:raise C.WinError(C.get_last_error())
