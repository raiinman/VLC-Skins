"""Run the private OSD interface against finite mocked VLC APIs, never VLC.

Test-only dependency: lupa (Lua 5.1/5.2), optionally provided with
--lua-python-path. The distributed support script needs no Python/lupa.
"""
import argparse
import importlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/nfs_volume_osd.lua'

HARNESS = r'''
local frames = FRAMES
local index, registrations, creations = 1, 0, 0
local events, stores = {}, {}
local channel_key = "nfs-volume-osd-slider-v1"
local function current() return frames[index] end
local function record(kind, value, channel)
    events[#events+1] = {kind=kind,value=value,channel=channel}
end
vlc = {
    volume={get=function()
        if current().read_error then error("transient volume read") end
        return current().raw
    end},
    object={vout=function()
        local name=current().vout
        if name == nil then return nil end
        stores[name]=stores[name] or {}
        return {name=name,vars=stores[name]}
    end},
    var={get=function(object, name)
        assert(object.name==current().vout, "Only current own vout may be read")
        if name=="fullscreen" then return current().fullscreen == true end
        assert(name==channel_key, "Unexpected variable read")
        if current().bad_channel then return "unrelated value" end
        if current().reserved_channel then return 1 end
        return object.vars[name]
    end,create=function(object,name,value)
        assert(object.name==current().vout and name==channel_key)
        assert(type(value)=="number" and value==math.floor(value))
        assert(value>=0 and value<=16777215)
        creations=creations+1; object.vars[name]=value; return 0
    end},
    osd={message=function(message,channel,position,duration)
        assert(current().vout ~= nil and channel==nil)
        assert(position=="top-right" and duration==1200000)
        if current().osd_error then error("vout disappeared") end
        record("message",message,channel)
    end,slider=function(position,kind,channel)
        assert(current().vout ~= nil)
        assert(position>=0 and position<=100 and kind=="vertical")
        assert(channel~=nil and channel>=8, "Text/default and slider channel must differ")
        record("slider",position,channel)
    end,channel_register=function()
        assert(current().vout ~= nil)
        registrations=registrations+1
        if current().invalid_registration then return -1 end
        return 7+registrations
    end},
    misc={mdate=function() return (index-1)*50000 end,
        mwait=function(deadline)
            assert(deadline==index*50000, "Polling must be 50ms")
            index=index+1
            if index>#frames then error("__TEST_DONE__") end
        end}
}
-- No filesystem, networking, process, desktop, playback or volume-write API
-- is supplied. The actual script is syntax-checked and executed unchanged.
io=nil; os=nil; require=nil
local chunk,syntax_error=loadstring(SCRIPT)
assert(chunk,syntax_error)
local ok,reason=pcall(chunk)
assert(not ok and string.find(tostring(reason),"__TEST_DONE__",1,true),tostring(reason))
ASSERTIONS
return #events
'''

CASES = [
    ('baseline', '{{raw=256,vout="a"},{raw=256,vout="a"}}',
     'assert(#events==0 and registrations==0 and creations==0)'),
    ('windowed percentages', '{{raw=256,vout="a"},{raw=128,vout="a"},{raw=128,vout="a"},{raw=384,vout="a"},{raw=0,vout="a"}}',
     'assert(#events==6 and events[1].value=="Volume 50%" and events[3].value=="Volume 150%" and events[5].value=="Volume 0%" and registrations==1); assert(events[2].value==50 and events[4].value==100 and events[6].value==0)'),
    ('fullscreen channels and new output', '{{raw=256,vout="a"},{raw=384,vout="a",fullscreen=true},{raw=128,vout="a",fullscreen=true},{raw=64,vout="b",fullscreen=true}}',
     'assert(#events==6 and registrations==2 and creations==2); assert(events[2].value==100 and events[4].value==50 and events[6].value==25); assert(events[2].channel==8 and events[4].channel==8 and events[6].channel==9)'),
    ('no current vout', '{{raw=256},{raw=128},{raw=128,vout="a"},{raw=64,vout="a"}}',
     'assert(#events==2 and events[1].value=="Volume 25%" and events[2].value==25 and registrations==1)'),
    ('invalid values do not create startup change', '{{},{raw=-1},{raw=0/0},{raw=math.huge},{raw=-math.huge},{raw="128"},{read_error=true},{raw=256,vout="a"},{raw=128,vout="a"}}',
     'assert(#events==2 and events[1].value=="Volume 50%" and events[2].value==50)'),
    ('rounding', '{{raw=256,vout="a"},{raw=257,vout="a"},{raw=258,vout="a"}}',
     'assert(#events==4 and events[1].value=="Volume 100%" and events[3].value=="Volume 101%")'),
    ('OSD disappearance does not stop observation', '{{raw=256,vout="a"},{raw=128,vout="a",osd_error=true},{raw=64,vout="a"}}',
     'assert(#events==2 and events[1].value=="Volume 25%" and events[2].value==25)'),
    ('existing wrong variable is not overwritten', '{{raw=256,vout="a"},{raw=128,vout="a",fullscreen=true,bad_channel=true}}',
     'assert(#events==1 and registrations==0 and creations==0)'),
    ('reserved text channel is not reused', '{{raw=256,vout="a"},{raw=128,vout="a",fullscreen=true,reserved_channel=true}}',
     'assert(#events==1 and registrations==0 and creations==0)'),
    ('invalid native channel is not used', '{{raw=256,vout="a"},{raw=128,vout="a",fullscreen=true,invalid_registration=true}}',
     'assert(#events==1 and registrations==1 and creations==0)'),
]


def run_cases(engine, source):
    for name, frames, assertions in CASES:
        runtime = engine.LuaRuntime(unpack_returned_tuples=True)
        # Lua 5.2 renamed loadstring; the shim is test harness only.
        runtime.execute('loadstring = loadstring or load')
        runtime.globals().SCRIPT = source
        harness = HARNESS.replace('FRAMES', frames).replace('ASSERTIONS', assertions)
        try:
            runtime.execute(harness)
        except Exception as error:
            raise AssertionError(f'{engine.__name__}: {name}: {error}') from error


def static_contract(source):
    source = re.sub(r'--[^\n]*', '', source)
    for forbidden in (r'vlc\.volume\.(?:set|up|down)', r'vlc\.(?:net|httpd|playlist)\.',
                      r'vlc\.var\.(?:set|trigger_callback|libvlc_command)',
                      r'\b(?:io|os)\.', r'\b(?:dofile|loadfile|require)\s*\('):
        assert not re.search(forbidden, source), forbidden
    assert source.count('vlc.var.create(') == 1
    launcher = (ROOT / 'tools/Start-NFS.ps1').read_text(encoding='utf-8-sig')
    builder = (ROOT / 'tools/build_effects.ps1').read_text(encoding='utf-8-sig')
    assert '--osd --extraintf=luaintf --lua-intf=nfs_volume_osd_v1' in launcher
    assert "$StartInfo.EnvironmentVariables['VLC_DATA_PATH']" in launcher
    assert not re.search(r'\$env:VLC_DATA_PATH\s*=', launcher)
    assert not re.search(r"EnvironmentVariables\['VLC_PLUGIN_PATH'\]\s*=", launcher)
    assert 'lua/intf/nfs_volume_osd_v1.lua' in launcher
    assert "'data/lua/intf'" in builder and "'nfs_volume_osd_v1.lua'" in builder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lua-python-path', type=Path)
    parser.add_argument('--support-dir', type=Path, help='Optional built skin-support directory to verify copied source bytes')
    args = parser.parse_args()
    if args.lua_python_path:
        sys.path.insert(0, str(args.lua_python_path.resolve()))
    source = SOURCE.read_text(encoding='utf-8')
    static_contract(source)
    if args.support_dir:
        assert (args.support_dir / 'data/lua/intf/nfs_volume_osd_v1.lua').read_bytes() == SOURCE.read_bytes()
        assert (args.support_dir.parent / 'Start-NFS.ps1').read_bytes() == (ROOT / 'tools/Start-NFS.ps1').read_bytes()
    try:
        engines = [importlib.import_module(f'lupa.lua{version}') for version in ('51', '52')]
    except ImportError as error:
        raise SystemExit('Static contracts passed; mocked execution requires test-only lupa (use --lua-python-path).') from error
    for engine in engines:
        run_cases(engine, source)
        # Prove checks reject fake startup changes and broken unit conversion.
        for mutation in (source.replace('last_volume ~= nil and ', ''),
                         source.replace('raw_volume * 100 / 256', 'raw_volume * 100 / 100')):
            try:
                run_cases(engine, mutation)
            except AssertionError:
                pass
            else:
                raise AssertionError('OSD regression mutation was accepted')
    lupa = importlib.import_module('lupa')
    print(f'PASS {len(CASES) * len(engines)} mocked OSD cases + 4 rejected mutations; lupa {lupa.__version__}, Lua5.1/5.2. No VLC/audio/UI/profile accessed.')


if __name__ == '__main__':
    main()
