"""Real Windows process-tree tests; no DS or solver calls."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PWSH=os.environ['DS_TEST_PWSH']

class NativeTests(unittest.TestCase):
    def run_native(self,body,timeout=5,payload=None,args=()):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        script=root/'fixture 中文.py';script.write_text(body,encoding='utf-8')
        inp=root/'input.txt'
        if payload is not None:inp.write_text(payload,encoding='utf-8')
        spec=dict(exe=sys.executable,arguments=[str(script),*args],cwd=str(root),
            stdout=str(root/'stdout'),stderr=str(root/'stderr'),receipt=str(root/'receipt.json'),
            timeout=timeout,outputBytes=1000000,inputFile=str(inp) if payload is not None else None)
        (root/'spec.json').write_text(json.dumps(spec),encoding='utf-8')
        p=subprocess.run([PWSH,'-NoProfile','-File',str(HERE/'author_job_process.ps1'),
            '-SpecFile',str(root/'spec.json')],capture_output=True,text=True,timeout=25)
        self.assertTrue((root/'receipt.json').exists(),p.stderr)
        receipt=json.loads((root/'receipt.json').read_text(encoding='utf-8-sig'))
        self.assertTrue(receipt['cleanupConfirmed'],(receipt,p.stderr))
        self.assertTrue(receipt['suspendedAssignment']);self.assertEqual(receipt['activeProcessesAfterCleanup'],0)
        return root,receipt

    def test_unicode_quoted_args_and_full_stdin(self):
        payload='完整指导 αβ 中文\n'*15000
        args=('含 空格','quote"here','backslash\\tail\\')
        root,r=self.run_native('import sys,json\nsys.stdin.reconfigure(encoding="utf-8")\nprint(json.dumps([sys.stdin.read(),sys.argv[1:]]))',payload=payload,args=args)
        self.assertEqual(r['exitCode'],0,(r,(root/'stderr').read_text()));self.assertTrue(r['stdinComplete'])
        self.assertEqual(json.loads((root/'stdout').read_text()),[payload,list(args)])

    def test_timeout_kills_sleeping_grandchild(self):
        body='import subprocess,sys,time\nsys.stdin.read()\np=subprocess.Popen([sys.executable,"-c","import time;time.sleep(90)"])\nprint(p.pid,flush=True)\ntime.sleep(90)'
        root,r=self.run_native(body,timeout=1.5,payload='hello')
        self.assertEqual(r['exitCode'],124,(r,(root/'stderr').read_text()));self.assertEqual(r['reason'],'timeout')
        self.assertTrue(r['stdinComplete']);self.assertTrue(r['terminationRequested'])
        self.assertTrue((root/'stdout').read_text().strip().isdigit())

    def test_normal_parent_exit_cleans_leftover_child(self):
        root,r=self.run_native('import subprocess,sys\nsubprocess.Popen([sys.executable,"-c","import time;time.sleep(90)"])\nprint("done")')
        self.assertEqual(r['exitCode'],0);self.assertTrue(r['terminationRequested'])
        self.assertEqual((root/'stdout').read_text().strip(),'done')

if __name__=='__main__':unittest.main(verbosity=2)
