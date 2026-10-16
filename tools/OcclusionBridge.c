/* Private-runtime-only pane occlusion filter. No installed file writes.
 * Exact VideoLAN3.0.23 plugin symbols/prologues and caller sites are pinned.
 */
#define CorrectWheel BaseCorrectWheel
#include "WheelBridge.c"
#undef CorrectWheel
#include <wincrypt.h>
#include <shlobj.h>
#include <intrin.h>
#include <stdint.h>
#include <wchar.h>
#include <string.h>

#define STATUS L"NfsOcclusionBridge.Status"
#define REJECT_FIRST L"NfsOcclusionBridge.RejectedFirst"
#define REJECT_SECOND L"NfsOcclusionBridge.RejectedSecond"
#define CAN_RVA 0x398b0
#define CHECK_RVA 0x5a070
#define FIRST_RETURN 0x5a3bb
#define SECOND_RETURN 0x5a3df
#define WINDOW_RVA 0x106590
#define HANDLE_RVA 0x40e40
#define INCREMENT_RVA 0x1a59b0
#define DEPEND_RVA 0x5bec0
#define DEPEND_RECURSIVE_CALL 0x5bfcb
#define SNAP_OFF L"NfsSkinWheelBridge.SnappingOff"
#define SNAP_SUPPORTED L"NfsOcclusionBridge.SnappingSupported"

typedef unsigned char (__fastcall *CanFn)(void *,void *,int *,int *);
typedef void (__fastcall *CheckFn)(void *,void *,int *,int *);
typedef void (__fastcall *DependFn)(void *,void *,void *);
typedef void *(__fastcall *ObjectFn)(void *);
typedef HWND (__fastcall *HandleFn)(void *);
typedef LONG (WINAPI *DwmFn)(HWND,DWORD,PVOID,DWORD);
static BYTE *plugin;
static CanFn original_can;
static CheckFn original_check;
static DependFn original_depend;
static unsigned int dependent_depth;
static DWORD ui_thread;
static HWND owner_bar;
static void *current_manager;
static BOOL installed;
static DwmFn dwm_attribute;
static BOOL file_digest(LPCWSTR path,BYTE digest[32]);
static HWND cached_targets[64];
static BOOL cached_exposure[64];
static int cached_count;
static void count_property(LPCWSTR name)
{
    SetPropW(owner_bar,name,(HANDLE)((ULONG_PTR)GetPropW(owner_bar,name)+1));
}
static const BYTE can_bytes[16]={0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54,0x55,0x57,0x56,0x53,0x48,0x83,0xec,0x58};
static const BYTE check_bytes[19]={0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54,0x55,0x57,0x56,0x53,0x48,0x81,0xec,0x98,0,0,0};
static const BYTE first_call[5]={0xe8,0xf5,0xf4,0xfd,0xff},second_call[5]={0xe8,0xd1,0xf4,0xfd,0xff};
static const BYTE window_bytes[5]={0x48,0x8b,0x41,0x10,0xc3};
static const BYTE handle_bytes[11]={0x48,0x8b,0x49,0x28,0x48,0x8b,0x01,0x48,0xff,0x60,0x40};
static const BYTE increment_bytes[16]={0x48,0x8b,0x41,0x18,0x48,0x85,0xc0,0x75,0x0a,0xeb,0x13,0x0f,0x1f,0x44,0x00,0x00};
static const BYTE depend_bytes[17]={0x41,0x54,0x55,0x57,0x56,0x53,0x48,0x83,0xec,0x60,0x4c,0x8b,0x25,0xcf,0x71,0x19,0x00};
static const BYTE depend_call[5]={0xe8,0xf0,0xfe,0xff,0xff};
static const BYTE moving_set_bytes[7]={0x48,0x8d,0x99,0xa0,0,0,0};

static BOOL readable(const void *address,SIZE_T size)
{
    uintptr_t start=(uintptr_t)address,end=start+size;
    if(!start||end<start)return FALSE;
    while(start<end) {
        MEMORY_BASIC_INFORMATION info;uintptr_t next;
        if(!VirtualQuery((void *)start,&info,sizeof(info))||info.State!=MEM_COMMIT||
           (info.Protect&(PAGE_NOACCESS|PAGE_GUARD))||!(info.Protect&(PAGE_READONLY|PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)))return FALSE;
        next=(uintptr_t)info.BaseAddress+info.RegionSize;
        if(next<=start)return FALSE;start=next;
    }
    return TRUE;
}
static BOOL skin_window(HWND window)
{
    DWORD pid=0;WCHAR name[32];
    return window&&GetWindowThreadProcessId(window,&pid)==ui_thread&&pid==GetCurrentProcessId()&&
        GetClassNameW(window,name,32)==15&&!lstrcmpW(name,L"SkinWindowClass");
}
static BOOL enabled(void)
{
    return installed&&GetCurrentThreadId()==ui_thread&&skin_window(owner_bar)&&
        (ULONG_PTR)GetPropW(owner_bar,PROP_ENABLED)==ENABLED_MARKER&&
        (ULONG_PTR)GetPropW(owner_bar,PROP_OWNER)==GetCurrentProcessId();
}
static BOOL CALLBACK find_owner(HWND window,LPARAM unused)
{
    UNREFERENCED_PARAMETER(unused);
    if(skin_window(window)&&(ULONG_PTR)GetPropW(window,PROP_ENABLED)==ENABLED_MARKER&&
       (ULONG_PTR)GetPropW(window,PROP_OWNER)==GetCurrentProcessId()) {owner_bar=window;return FALSE;}
    return TRUE;
}
static BOOL private_runtime(HMODULE module)
{
    WCHAR executable[MAX_PATH],path[MAX_PATH],root[MAX_PATH],*slash,*hash,*marker;
    DWORD n=GetModuleFileNameW(NULL,executable,MAX_PATH),length;SIZE_T i;BYTE digest[32];WCHAR hash_text[65];
    if(!n||n>=MAX_PATH)return FALSE;
    slash=wcsrchr(executable,L'\\');if(!slash||_wcsicmp(slash+1,L"vlc.exe"))return FALSE;
    *slash=0;wcscpy_s(root,MAX_PATH,executable);
    hash=wcsrchr(root,L'\\');if(!hash||wcslen(hash+1)!=64)return FALSE;
    for(i=1;i<=64;i++)if(!((hash[i]>=L'0'&&hash[i]<=L'9')||(hash[i]>=L'a'&&hash[i]<=L'f')))return FALSE;
    { WCHAR full[MAX_PATH];DWORD full_n=GetModuleFileNameW(NULL,full,MAX_PATH);
      if(!full_n||full_n>=MAX_PATH||!file_digest(full,digest))return FALSE; }
    for(i=0;i<32;i++)swprintf_s(hash_text+i*2,65-i*2,L"%02x",digest[i]);
    if(_wcsicmp(hash+1,hash_text))return FALSE;
    *hash=0;marker=wcsrchr(root,L'\\');if(!marker||_wcsicmp(marker+1,L"VlcRuntime"))return FALSE;
    wcscpy_s(root,MAX_PATH,executable);length=(DWORD)wcslen(root);
    if(length+40>=MAX_PATH)return FALSE;
    wcscpy_s(path,MAX_PATH,root);wcscat_s(path,MAX_PATH,L"\\portable");
    if(GetFileAttributesW(path)==INVALID_FILE_ATTRIBUTES||!(GetFileAttributesW(path)&FILE_ATTRIBUTE_DIRECTORY))return FALSE;
    n=GetModuleFileNameW(module,path,MAX_PATH);if(!n||n>=MAX_PATH)return FALSE;
    wcscat_s(root,MAX_PATH,L"\\plugins\\gui\\libskins2_plugin.dll");
    if(!_wcsicmp(path,root))return TRUE;
    /* The companion also supports a private copied executable using the
     * standard installed plugin. Only its own process mapping is patched;
     * the installed executable still fails the private-runtime checks above. */
    if(SHGetFolderPathW(NULL,CSIDL_PROGRAM_FILES,NULL,SHGFP_TYPE_CURRENT,root)!=S_OK)return FALSE;
    if(wcslen(root)+wcslen(L"\\VideoLAN\\VLC\\plugins\\gui\\libskins2_plugin.dll")>=MAX_PATH)return FALSE;
    wcscat_s(root,MAX_PATH,L"\\VideoLAN\\VLC\\plugins\\gui\\libskins2_plugin.dll");
    return !_wcsicmp(path,root);
}
static BOOL file_digest(LPCWSTR path,BYTE digest[32])
{
    HCRYPTPROV provider=0;HCRYPTHASH hash=0;HANDLE file=INVALID_HANDLE_VALUE;
    BYTE bytes[32768];DWORD read=0,size=32;BOOL ok=FALSE;
    file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,0,NULL);
    if(file==INVALID_HANDLE_VALUE)return FALSE;
    if(!CryptAcquireContextW(&provider,NULL,NULL,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)||!CryptCreateHash(provider,CALG_SHA_256,0,0,&hash))goto done;
    for(;;) {
        if(!ReadFile(file,bytes,sizeof(bytes),&read,NULL))goto done;
        if(!read)break;
        if(!CryptHashData(hash,bytes,read,0))goto done;
    }
    ok=CryptGetHashParam(hash,HP_HASHVAL,digest,&size,0)&&size==32;
done:
    if(hash)CryptDestroyHash(hash);if(provider)CryptReleaseContext(provider,0);CloseHandle(file);return ok;
}
static BOOL hash_plugin(HMODULE module)
{
    static const BYTE expected[32]={0xc8,0x8b,0x5d,0x37,0xfd,0x55,0x4a,0x96,0x85,0x08,0xd2,0xd2,0x0c,0xe4,0xce,0xc2,0x27,0x91,0x34,0xb9,0x84,0x0c,0x05,0xad,0xba,0x98,0x9b,0x25,0xd8,0x46,0x82,0xc5};
    WCHAR path[MAX_PATH];BYTE digest[32];DWORD n=GetModuleFileNameW(module,path,MAX_PATH);
    return n&&n<MAX_PATH&&file_digest(path,digest)&&!memcmp(digest,expected,32);
}
static HWND object_handle(void *object)
{
    HWND result=NULL;
    if(!readable(object,0x30))return NULL;
    __try {result=((HandleFn)(plugin+HANDLE_RVA))(object);} __except(EXCEPTION_EXECUTE_HANDLER) {return NULL;}
    return skin_window(result)?result:NULL;
}
static HWND anchor_handle(void *anchor)
{
    void *layout,*window;
    if(!readable(anchor,0x68))return NULL;
    layout=*(void **)((BYTE *)anchor+0x60);if(!readable(layout,0x18))return NULL;
    window=((ObjectFn)(plugin+WINDOW_RVA))(layout);return object_handle(window);
}
static BOOL moving_windows(HWND *windows,int *count)
{
    BYTE *head;void *node;int n=0,j;
    if(!current_manager||!readable(current_manager,0xc0))return FALSE;
    head=(BYTE *)current_manager+0xa8;node=*(void **)(head+0x10);
    while(node!=head) {
        void *object;HWND window;
        if(n>=64||!readable(node,0x28))return FALSE;
        object=*(void **)((BYTE *)node+0x20);window=object_handle(object);if(!window)return FALSE;
        for(j=0;j<n;j++)if(windows[j]==window)return FALSE;
        windows[n++]=window;
        __try {node=((ObjectFn)(plugin+INCREMENT_RVA))(node);} __except(EXCEPTION_EXECUTE_HANDLER) {return FALSE;}
    }
    if(!n)return FALSE;*count=n;return TRUE;
}
static BOOL member(HWND window,HWND *moving,int count)
{
    int i;for(i=0;i<count;i++)if(window==moving[i])return TRUE;return FALSE;
}
static HRGN screen_region(HWND window)
{
    RECT bounds;HRGN region;int result;
    if(!GetWindowRect(window,&bounds)||bounds.right<=bounds.left||bounds.bottom<=bounds.top)return NULL;
    region=CreateRectRgn(0,0,0,0);if(!region)return NULL;
    result=GetWindowRgn(window,region);
    if(result==ERROR) {if(!SetRectRgn(region,0,0,bounds.right-bounds.left,bounds.bottom-bounds.top)){DeleteObject(region);return NULL;}}
    if(OffsetRgn(region,bounds.left,bounds.top)==ERROR){DeleteObject(region);return NULL;}return region;
}
static BOOL opaque_window(HWND window)
{
    LONG_PTR style=GetWindowLongPtrW(window,GWL_EXSTYLE);DWORD cloak=0;
    if(!IsWindowVisible(window)||IsIconic(window)||(style&WS_EX_TRANSPARENT))return FALSE;
    if(!dwm_attribute||dwm_attribute(window,14,&cloak,sizeof(cloak))<0||cloak)return FALSE;
    if(style&WS_EX_LAYERED) {
        COLORREF key;BYTE alpha;DWORD flags;
        if(!GetLayeredWindowAttributes(window,&key,&alpha,&flags)||flags!=LWA_ALPHA||alpha!=255)return FALSE;
    }
    return TRUE;
}
/* TRUE means uncertain/exposed. Only proven empty visible region rejects. */
static BOOL exposed_target(HWND target,HWND *moving,int count)
{
    HWND above;HRGN remaining=screen_region(target);int iterations=0;
    if(!remaining)return TRUE;
    for(above=GetTopWindow(NULL);above&&above!=target;above=GetWindow(above,GW_HWNDNEXT)) {
        HRGN cover;int result;
        if(++iterations>2048){DeleteObject(remaining);return TRUE;}
        if(above==owner_bar||member(above,moving,count)||!opaque_window(above))continue;
        cover=screen_region(above);if(!cover)continue;
        result=CombineRgn(remaining,remaining,cover,RGN_DIFF);DeleteObject(cover);
        if(result==ERROR){DeleteObject(remaining);return TRUE;}
        if(result==NULLREGION){DeleteObject(remaining);return FALSE;}
    }
    DeleteObject(remaining);return TRUE;
}
static BOOL cached_target_exposed(HWND target,HWND *moving,int count)
{
    int i;BOOL result;
    for(i=0;i<cached_count;i++)if(cached_targets[i]==target)return cached_exposure[i];
    result=exposed_target(target,moving,count);
    if(cached_count<64){cached_targets[cached_count]=target;cached_exposure[cached_count++]=result;}
    return result;
}
static unsigned char __fastcall filtered_can(void *first,void *second,int *x,int *y)
{
    uintptr_t caller=(uintptr_t)_ReturnAddress()-(uintptr_t)plugin;
    count_property(L"NfsOcclusionBridge.CanCalls");
    if(enabled()&&(caller==FIRST_RETURN||caller==SECOND_RETURN)) {
        /* GCC places the source's first (stationary-this) call at the higher
         * address; the lower call is the reversed fallback using -offsets. */
        HWND target=anchor_handle(caller==SECOND_RETURN?first:second),moving[64];int count=0;
        BOOL valid_moving=moving_windows(moving,&count);
        count_property(caller==FIRST_RETURN?L"NfsOcclusionBridge.FirstCalls":L"NfsOcclusionBridge.SecondCalls");
        if(!target)count_property(L"NfsOcclusionBridge.InvalidTarget");
        if(!valid_moving)count_property(L"NfsOcclusionBridge.InvalidMoving");
        if(target&&valid_moving&&member(target,moving,count))count_property(L"NfsOcclusionBridge.TargetMoving");
        if(target&&valid_moving&&!member(target,moving,count)&&!cached_target_exposed(target,moving,count)) {
            LPCWSTR prop=caller==FIRST_RETURN?REJECT_FIRST:REJECT_SECOND;
            SetPropW(owner_bar,prop,(HANDLE)((ULONG_PTR)GetPropW(owner_bar,prop)+1));return 0;
        }
        if(target&&valid_moving&&!member(target,moving,count))count_property(L"NfsOcclusionBridge.Exposed");
    }
    return original_can(first,second,x,y);
}
static void __fastcall contextual_check(void *manager,void *window,int *x,int *y)
{
    void *previous=current_manager;
    if(GetCurrentThreadId()!=ui_thread){original_check(manager,window,x,y);return;}
    if(enabled()&&(ULONG_PTR)GetPropW(owner_bar,SNAP_OFF)==1) {
        count_property(L"NfsOcclusionBridge.SnapBypasses");return;
    }
    count_property(L"NfsOcclusionBridge.CheckCalls");
    current_manager=manager;cached_count=0;
    __try {original_check(manager,window,x,y);} __finally {current_manager=previous;}
}
static void __fastcall independent_depend(void *manager,void *set,void *window)
{
    if(enabled()&&((ULONG_PTR)GetPropW(owner_bar,SNAP_OFF)==1||dependent_depth)) {
        /* Native startMove passes its moving set at +0xa0. Keep its native
         * initial insertion, but exclude recursive dependents. Resize uses
         * separate dependency sets, which remain empty while OFF. */
        if(readable(manager,0xd0)&&object_handle(window)) {
            if(set!=(BYTE *)manager+0xa0||dependent_depth) {
                count_property(L"NfsOcclusionBridge.DependentBypasses");return;
            }
            dependent_depth++;
            __try {original_depend(manager,set,window);} __finally {dependent_depth--;}
            return;
        }
    }
    original_depend(manager,set,window);
}
static void absolute_jump(BYTE *destination,const void *target)
{
    destination[0]=0xff;destination[1]=0x25;memset(destination+2,0,4);memcpy(destination+6,&target,8);
}
static void *trampoline(BYTE *code,SIZE_T length)
{
    BYTE *copy=(BYTE *)VirtualAlloc(NULL,length+14,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);DWORD old;
    if(!copy)return NULL;memcpy(copy,code,length);absolute_jump(copy+length,code+length);
    if(!VirtualProtect(copy,length+14,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),copy,length+14)){VirtualFree(copy,0,MEM_RELEASE);return NULL;}
    return copy;
}
static void *depend_trampoline(void)
{
    BYTE *copy=(BYTE *)VirtualAlloc(NULL,38,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    BYTE *target;int32_t displacement;DWORD old;
    if(!copy)return NULL;
    /* Relocate only the pinned mov r12,[rip+disp32]. The two replacement
     * instructions have the same register/flags result and need no near RVA. */
    memcpy(&displacement,plugin+DEPEND_RVA+13,4);
    target=plugin+DEPEND_RVA+17+displacement;
    if(!readable(target,8)){VirtualFree(copy,0,MEM_RELEASE);return NULL;}
    memcpy(copy,plugin+DEPEND_RVA,10);
    copy[10]=0x49;copy[11]=0xbc;memcpy(copy+12,&target,8);
    copy[20]=0x4d;copy[21]=0x8b;copy[22]=0x24;copy[23]=0x24;
    absolute_jump(copy+24,plugin+DEPEND_RVA+17);
    if(!VirtualProtect(copy,38,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),copy,38)) {
        VirtualFree(copy,0,MEM_RELEASE);return NULL;
    }
    return copy;
}
static BOOL patch(BYTE *code,SIZE_T length,const void *target)
{
    BYTE bytes[32];DWORD old,unused;BOOL ok;
    if(length>sizeof(bytes)||!VirtualProtect(code,length,PAGE_EXECUTE_READWRITE,&old))return FALSE;
    memset(bytes,0x90,length);absolute_jump(bytes,target);memcpy(code,bytes,length);
    ok=FlushInstructionCache(GetCurrentProcess(),code,length);
    if(!VirtualProtect(code,length,old,&unused))ok=FALSE;
    return ok;
}
static void install(void)
{
    HMODULE module,self,dwm;static BOOL attempted=FALSE;
    if(installed||attempted)return;
    ui_thread=GetCurrentThreadId();EnumThreadWindows(ui_thread,find_owner,0);
    if(!owner_bar)return;
    module=GetModuleHandleW(L"libskins2_plugin.dll");if(!module)return;
    attempted=TRUE;plugin=(BYTE *)module;
    if(!private_runtime(module)||!hash_plugin(module)){SetPropW(owner_bar,STATUS,(HANDLE)2);return;}
    if(!readable(plugin+CAN_RVA,16)||!readable(plugin+CHECK_RVA,0x33c)||!readable(plugin+WINDOW_RVA,5)||!readable(plugin+HANDLE_RVA,11)||!readable(plugin+INCREMENT_RVA,16)||
       memcmp(plugin+CAN_RVA,can_bytes,16)||memcmp(plugin+CHECK_RVA,check_bytes,19)||
       memcmp(plugin+FIRST_RETURN-5,first_call,5)||memcmp(plugin+SECOND_RETURN-5,second_call,5)||
       memcmp(plugin+WINDOW_RVA,window_bytes,5)||memcmp(plugin+HANDLE_RVA,handle_bytes,11)||
       memcmp(plugin+INCREMENT_RVA,increment_bytes,16)||
       !readable(plugin+DEPEND_RVA,17)||!readable(plugin+DEPEND_RECURSIVE_CALL,5)||!readable(plugin+0x5bffe,7)||
       memcmp(plugin+DEPEND_RVA,depend_bytes,17)||memcmp(plugin+DEPEND_RECURSIVE_CALL,depend_call,5)||
       memcmp(plugin+0x5bffe,moving_set_bytes,7)){SetPropW(owner_bar,STATUS,(HANDLE)3);return;}
    original_can=(CanFn)trampoline(plugin+CAN_RVA,16);original_check=(CheckFn)trampoline(plugin+CHECK_RVA,19);
    original_depend=(DependFn)depend_trampoline();
    if(!original_can||!original_check||!original_depend){SetPropW(owner_bar,STATUS,(HANDLE)4);return;}
    /* Pin all branch targets before the first patch. Never unload patched code. */
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,(LPCWSTR)(ULONG_PTR)&filtered_can,&self)){SetPropW(owner_bar,STATUS,(HANDLE)5);return;}
    dwm=LoadLibraryExW(L"dwmapi.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
    if(dwm)dwm_attribute=(DwmFn)(ULONG_PTR)GetProcAddress(dwm,"DwmGetWindowAttribute");
    if(!patch(plugin+CHECK_RVA,19,(const void *)(ULONG_PTR)&contextual_check)||!patch(plugin+CAN_RVA,16,(const void *)(ULONG_PTR)&filtered_can)||
       !patch(plugin+DEPEND_RVA,17,(const void *)(ULONG_PTR)&independent_depend)){SetPropW(owner_bar,STATUS,(HANDLE)6);return;}
    installed=TRUE;SetPropW(owner_bar,SNAP_SUPPORTED,(HANDLE)1);SetPropW(owner_bar,STATUS,(HANDLE)1);
}
__declspec(dllexport) LRESULT CALLBACK CorrectWheel(int code,WPARAM removed,LPARAM payload)
{
    if(code==HC_ACTION&&removed==PM_REMOVE&&payload)install();
    return BaseCorrectWheel(code,removed,payload);
}
