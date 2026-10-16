"""Run synthetic cross-process wheel-DLL proof on a private non-input desktop.

No VLC/helper instance, real input, foreground change or user-profile write.
The owner job terminates only this fixture and its synthetic child window.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from check_hover_native import ROOT, OwnedJob, sha
from windows_load_host import DesktopProcess, ProcessGuard, input_desktop


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dll',type=Path,required=True)
    parser.add_argument('--protect-pid',type=int,action='append',default=[])
    parser.add_argument('--guard-file',type=Path,action='append',default=[])
    args=parser.parse_args();output=args.output.resolve();scratch=(ROOT.parent/'work').resolve()
    if not output.is_relative_to(scratch) or output==scratch:parser.error('Output must be a new work/ subdirectory')
    output.mkdir(parents=True,exist_ok=False)
    dll=output/'NfsWheelBridge64.dll';shutil.copyfile(args.dll,dll)
    source=output/'check_wheel_native.cs';source.write_bytes((ROOT/'tools/check_wheel_native.cs').read_bytes())
    exe=output/'WheelNativeFixture.exe'
    compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    built=subprocess.run([str(compiler),'/nologo','/platform:x64','/target:winexe','/optimize+','/reference:System.Web.Extensions.dll','/out:'+str(exe),str(source)],capture_output=True,text=True)
    if built.returncode:raise RuntimeError(built.stdout+built.stderr)
    paths=list(dict.fromkeys([Path(os.environ['APPDATA'])/'vlc/vlcrc',Path(os.environ['APPDATA'])/'vlc/vlc-qt-interface.ini',*args.guard_file]))
    before={str(p):sha(p) for p in paths};desktop=input_desktop();guards=[];job=None;process=None;report={'passed':False};errors=[]
    result=output/'fixture.json'
    try:
        for pid in args.protect_pid:guards.append(ProcessGuard(pid))
        env=dict(os.environ);env['TEMP']=env['TMP']=str(output)
        process=DesktopProcess([str(exe),str(dll),str(result)],env);job=OwnedJob(process)
        Path(str(result)+'.ready').write_text('Owned job armed\n')
        status=process.wait(45)
        if result.exists():report=json.loads(result.read_text(encoding='utf-8-sig'))
        report['fixture_exit_code']=status
    finally:
        for item in (job,process):
            if item is not None:
                try:item.close()
                except Exception as error:errors.append(str(error))
        after={str(p):sha(p) for p in paths}
        report.update(cleanup_errors=errors,input_desktop_unchanged=input_desktop()==desktop,guarded_files_unchanged=before==after,
                      protected_processes=[dict(pid=g.pid,alive=g.alive()) for g in guards],owned_fixture_closed=process is not None and process.handle is None,
                      dll_sha256=sha(dll),fixture_source_sha256=sha(source),fixture_sha256=sha(exe))
        for guard in guards:guard.close()
        report['passed']=bool(report.get('passed') and report.get('fixture_exit_code')==0 and not errors and report['input_desktop_unchanged'] and report['guarded_files_unchanged'] and report['owned_fixture_closed'] and all(p['alive'] for p in report['protected_processes']))
        (output/'preservation.json').write_text(json.dumps(dict(before=before,after=after),indent=2))
        (output/'result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(passed=report['passed'],cases=len(report.get('cases',[])),report=str(output/'result.json'))))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
