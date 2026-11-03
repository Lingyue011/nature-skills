"""Inject upstream failures through the real transport/controller, no network."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
PLOT=BASE/'runtime/plot'
ORG=BASE/'runtime/organization'
sys.path.insert(0,str(ORG));sys.path.insert(0,str(PLOT))
import plot_worker as plot
import model_transport as organization_transport
import organization_worker as org
import role_retry


def fake_native(failure='truncated_stream',answers=None,always=False):
    counts={};sessions={}
    def invoke(worker,exe,args,cwd,stem,seconds):
        folder=Path(cwd);role=folder.name.split('_')[1]
        if stem.name=='request':
            counts[role]=counts.get(role,0)+1
            uid=f'ses_{role}_{counts[role]}'
            fail=role=='B' and (always or counts[role]==1)
            answer=answers(role) if answers else dict(role=role,ok=True)
            model=dict(id='deepseek-v4.1-flash',providerID='opencode-go',variant='max')
            if fail and failure=='wrong_model':model['variant']='high'
            session=dict(info=dict(id=uid,outcome='succeeded',model=model,tokens={},cost=0),messages=[dict(type='assistant',model=model)])
            sessions[uid]=session
            events=[dict(type='step_start',sessionID=uid),dict(type='text',sessionID=uid,part=dict(text=json.dumps(answer)))]
            native=dict(exitCode=0,reason=None,pid=0,seconds=.01)
            if fail:
                if failure in ('http503','auth401'):
                    events=[dict(type='error',sessionID=uid,error=dict(status=503 if failure=='http503' else 401,message='upstream request failed'))]
                if failure=='tool_event':events.insert(1,dict(type='tool_use',sessionID=uid,part=dict(tool='read')))
                if failure=='truncated_answer':events[-1]['part']['text']='{"ok":'
                if failure=='changed_config':(folder/'opencode.json').write_text('{}',encoding='utf-8')
                if failure=='timeout':native.update(exitCode=124,reason='timeout')
            raw='\n'.join(json.dumps(e) for e in events)+'\n'
            if fail and failure=='truncated_stream':raw=json.dumps(events[0])+'\n'+raw[:20]
            Path(str(stem)+'.stdout').write_text(raw,encoding='utf-8')
            plot.write(str(stem)+'.native.json',native)
            if native['exitCode']:raise RuntimeError('Native failure: owned timeout')
            return raw
        session=sessions[args[-1]]
        raw=json.dumps(session)
        Path(str(stem)+'.stdout').write_text(raw,encoding='utf-8')
        plot.write(str(stem)+'.native.json',dict(exitCode=0,reason=None,pid=0,seconds=.01))
        return raw
    return invoke,counts


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.sleep=patch.object(role_retry.time,'sleep',return_value=None);self.sleep.start();self.addCleanup(self.sleep.stop)

    def worker(self,cls,sub,**extra):
        run=self.root/sub;run.mkdir()
        return cls(dict(max_rounds=2,wall_seconds=120,turn_seconds=30,**extra),run,'unused','unused')

    def test_replacement_keeps_completed_roles_for_both_workers(self):
        for name,cls in [('plot',plot.Worker),('org',organization_transport.Worker)]:
            with self.subTest(worker=name):
                worker=self.worker(cls,name);native,counts=fake_native()
                with patch.object(cls,'native',new=native):
                    worker.turn('A',1,'same task')
                    original=plot.sha(worker.run/'01_A/receipt.json')
                    for role in ['B','C','D']:self.assertEqual(worker.turn(role,1,'same task')['role'],role)
                self.assertEqual(counts,dict(A=1,B=2,C=1,D=1))
                self.assertEqual(plot.sha(worker.run/'01_A/receipt.json'),original)
                self.assertEqual(worker.calls,4);self.assertEqual(worker.replacements,1)
                self.assertTrue((worker.run/'01_B/attempt_failure.json').exists())
                self.assertEqual(plot.read(worker.run/'01_B_retry02/receipt.json')['attempt'],2)

    def test_recovers_known_upstream_modes(self):
        for mode in ['truncated_answer','http503','timeout']:
            with self.subTest(mode=mode):
                worker=self.worker(plot.Worker,mode);native,counts=fake_native(mode)
                with patch.object(plot.Worker,'native',new=native):self.assertTrue(worker.turn('B',1,'same task')['ok'])
                self.assertEqual(counts['B'],2)

    def test_integrity_model_tool_and_auth_fail_without_replacement(self):
        for mode in ['wrong_model','tool_event','changed_config','auth401']:
            with self.subTest(mode=mode):
                worker=self.worker(plot.Worker,mode);native,counts=fake_native(mode)
                with patch.object(plot.Worker,'native',new=native),self.assertRaises(Exception):worker.turn('B',1,'same task')
                self.assertEqual(counts['B'],1);self.assertEqual(worker.replacements,0)

    def test_bounded_attempts_and_job_replacement_budget(self):
        for name,extras,expected in [('perrole',{},3),('perjob',{'max_replacements':0},1)]:
            worker=self.worker(plot.Worker,name,**extras);native,counts=fake_native('http503',always=True)
            with patch.object(plot.Worker,'native',new=native),self.assertRaises(Exception):worker.turn('B',1,'same task')
            self.assertEqual(counts['B'],expected)

    def test_complete_malformed_json_is_not_truncation(self):
        self.assertFalse(role_retry.incomplete('{"ok": wrong}'))
        self.assertFalse(role_retry.incomplete('Here is the answer'))
        self.assertTrue(role_retry.incomplete('{"ok":'))

    def test_actual_organization_controller_continues_C_D_after_B_failure(self):
        repo=self.root/'repo';repo.mkdir();(repo/'cache.bin').write_bytes(b'cache')
        (repo/'keep.py').write_text('# active',encoding='utf-8')
        closure=self.root/'closure.json';plot.write(closure,dict(scope='test fixture only'))
        job=dict(repository=str(repo),roles=4,turn_seconds=30,wall_seconds=120,task='fixture',
                 closure_review=str(closure),closure_sha256=plot.sha(closure),protected_paths=['keep.py'],
                 candidates=[dict(path='cache.bin',eligible=True,note='test fixture'),dict(path='keep.py',eligible=False,note='protected')])
        jobfile=self.root/'job.json';plot.write(jobfile,job)
        def answer(role):
            if role in ('A','D'):return dict(entries=[dict(id='F001',action='move',reason='cache'),dict(id='F002',action='keep',reason='source')],summary='test')
            return dict(verdict='accept',blocking_ids=[],findings=[])
        native,counts=fake_native(answers=answer)
        with patch.object(org.Worker,'native',new=native):
            result=org.plan(jobfile,self.root/'outside_runs','unused','unused')
        self.assertEqual(result['status'],'proposed_pending_root_review')
        self.assertEqual(counts,dict(A=1,B=2,C=1,D=1))
        self.assertEqual(result['proposed_files'],1)
        self.assertEqual(result['replacements_used'],1)
        self.assertEqual(len(result['sessions']),4)


if __name__=='__main__':unittest.main(verbosity=2)
