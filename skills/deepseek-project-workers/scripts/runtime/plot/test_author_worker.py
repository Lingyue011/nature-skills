"""Offline state-machine tests. Model is mocked; candidate fixture really renders."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import author_worker as a

SOURCE='''import argparse,json
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--inputs');p.add_argument('--output');x=p.parse_args()
o=Path(x.output);o.mkdir()
Image.new('RGB',(600,400),'white').save(o/'figure.png')
Image.new('RGB',(600,400),'white').save(o/'preview.png')
(o/'qa.json').write_text(json.dumps({'passed':True,'fixture':'rendered'}))
'''


class AuthorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        inp=self.root/'data.json';inp.write_text('{"immutable":1}')
        exe=self.root/'renderer.exe';exe.write_bytes(b'fixture-not-launched')
        job=dict(inputs=[str(inp)],approved_sha256={str(inp):a.sha(inp)},
            renderer_exe=str(exe),renderer_sha256=a.sha(exe),task='Fixture',
            input_contract='Use immutable value',max_rounds=2,turn_seconds=300,
            wall_seconds=1200,render_seconds=30,role_retries=0,max_replacements=0)
        path=self.root/'job.json';a.write(path,job)
        self.run,self.state=a.start(path,self.root/'runs',str(exe),str(exe))

    def tearDown(self):self.tmp.cleanup()

    def propose(self):
        with patch.object(a.Worker,'turn',return_value=dict(source=SOURCE,summary='DS fixture')):
            a.propose(self.state,self.run)

    def test_author_pauses_without_render(self):
        self.propose()
        self.assertEqual(self.state['status'],'pending_code_review')
        self.assertFalse((self.run/'01_render').exists())
        self.assertEqual((self.run/'01_candidate.py').read_text(),SOURCE)

    def test_approval_binds_code_inputs_runtime_controller(self):
        self.propose();good=a.request_contract(self.state,self.run)
        for field in ('run_id','round','source_sha256','input_hashes','renderer_exe','controllers','executables'):
            bad=copy.deepcopy(good);bad[field]='wrong'
            with self.subTest(field=field),self.assertRaises(ValueError):
                a.validate_approval(self.state,self.run,bad)
        a.validate_approval(self.state,self.run,good)
        (self.run/'01_candidate.py').write_text(SOURCE+'\n# changed')
        with self.assertRaises(ValueError):a.validate_approval(self.state,self.run,good)

    def test_changed_original_or_copy_blocks(self):
        self.propose();p=next((self.run/'inputs').iterdir());p.write_text('changed')
        with self.assertRaises(ValueError):a.check_immutable(self.state)

    def test_wall_includes_pause_and_state_not_reset(self):
        self.propose();self.state['started_epoch']-=1201
        with self.assertRaises(TimeoutError):a.check_immutable(self.state)
        self.assertEqual(self.state['round'],1)

    def test_no_replay_after_inflight_or_terminal(self):
        self.propose();approval=a.request_contract(self.state,self.run)
        for status in ('render_running','review_running','author_running','candidate_ready_pending_root_review'):
            self.state['status']=status
            with self.subTest(status=status),self.assertRaises(ValueError):a.validate_approval(self.state,self.run,approval)

    def native_render(self,exe,args,cwd,stem,seconds):
        p=subprocess.run([sys.executable,*args],cwd=cwd,capture_output=True,text=True,timeout=seconds)
        self.assertEqual(p.returncode,0,p.stderr)
        return p.stdout

    def test_accept_real_render_and_vision(self):
        self.propose();approval=a.request_contract(self.state,self.run)
        b=dict(verdict='accept',vision_probe='ABCDEF',findings=[],summary='fixture')
        with patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.Worker,'turn',return_value=b),patch.object(a.secrets,'token_hex',return_value='abcdef'):
            a.resume(self.state,self.run,approval)
        self.assertEqual(self.state['status'],'candidate_ready_pending_root_review')
        self.assertTrue((self.run/'01_render'/'figure.png').is_file())

    def test_revision_returns_to_source_review(self):
        self.propose();approval=a.request_contract(self.state,self.run);seen=[]
        def turn(role,n,prompt,attachments):
            seen.append(role)
            if role=='B':return dict(verdict='revise',vision_probe='ABCDEF',findings=['change style'])
            self.assertIn('change style',prompt)
            return dict(source=SOURCE+'\n# DS revision',summary='revision')
        with patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.Worker,'turn',side_effect=turn),patch.object(a.secrets,'token_hex',return_value='abcdef'):
            a.resume(self.state,self.run,approval)
        self.assertEqual(seen,['B','A']);self.assertEqual(self.state['status'],'pending_code_review')
        self.assertEqual(self.state['round'],2);self.assertFalse((self.run/'02_render').exists())

    def test_wrong_probe_rejects(self):
        self.propose();approval=a.request_contract(self.state,self.run)
        with patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.Worker,'turn',return_value=dict(verdict='accept',vision_probe='BAD',findings=[])),self.assertRaisesRegex(ValueError,'probe'):
            a.resume(self.state,self.run,approval)

    def test_round_limit(self):
        self.state['job']['max_rounds']=1
        a.write(self.run/'job.json',self.state['job']);self.state['frozen'][str(self.run/'job.json')]=a.sha(self.run/'job.json')
        self.propose();approval=a.request_contract(self.state,self.run)
        with patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.Worker,'turn',return_value=dict(verdict='revise',vision_probe='ABCDEF',findings=[])),patch.object(a.secrets,'token_hex',return_value='abcdef'):
            a.resume(self.state,self.run,approval)
        self.assertEqual(self.state['status'],'round_limit_pending_root_review')

    def test_lock_exclusive(self):
        with a.lock(self.run):
            with self.assertRaises(FileExistsError):
                with a.lock(self.run):pass

    def test_persisted_budget_tampering_rejected(self):
        self.state['job']['wall_seconds']=2400
        with self.assertRaisesRegex(ValueError,'frozen job'):a.check_immutable(self.state)

    def test_extra_input_rejected(self):
        (self.run/'inputs'/'extra.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'membership'):a.check_immutable(self.state)

    def test_changed_executable_rejected(self):
        self.state['pwsh']='other.exe'
        with self.assertRaisesRegex(ValueError,'paths'):a.check_immutable(self.state)

    def test_guidance_reaches_both_roles_and_is_frozen(self):
        skill=self.root/'SKILL.md';skill.write_text('Civil guide: preserve axes')
        recipe=self.root/'paraview-recipes.md';recipe.write_text('Use actual finite element geometry')
        job=copy.deepcopy(self.state['job']);job.update(figure_profile='generic',
            guidance_files=[str(skill),str(recipe)],
            approved_guidance_sha256={str(p):a.sha(p) for p in (skill,recipe)})
        a.write(self.root/'guided.json',job)
        run,state=a.start(self.root/'guided.json',self.root/'guided_runs',job['renderer_exe'],job['renderer_exe'])
        prompts=[]
        def turn(role,n,prompt,attachments):
            prompts.append((role,json.loads(prompt)))
            if role=='A':return dict(source=SOURCE)
            return dict(verdict='accept',vision_probe='ABCDEF',findings=[])
        with patch.object(a.Worker,'turn',side_effect=turn),patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.secrets,'token_hex',return_value='abcdef'):
            a.propose(state,run);a.resume(state,run,a.request_contract(state,run))
        self.assertEqual([p[0] for p in prompts],['A','B'])
        for role,prompt in prompts:
            self.assertEqual(prompt['figure_profile'],'generic')
            self.assertEqual(len(prompt['presentation_guidance']),2)
            self.assertIn('preserve axes',prompt['presentation_guidance'][0]['content'])
        (run/'guidance'/'00-SKILL.md').write_text('changed')
        with self.assertRaises(ValueError):a.check_immutable(state)

    def test_prompt_budget_and_missing_civil_guidance(self):
        with self.assertRaisesRegex(ValueError,'prompt budget'):
            a.guided_prompt(self.state,self.run,dict(too_long='x'*29000))
        job=copy.deepcopy(self.state['job']);job['figure_profile']='civil-paraview'
        a.write(self.root/'invalid.json',job)
        with self.assertRaisesRegex(ValueError,'incomplete'):
            a.start(self.root/'invalid.json',self.root/'invalid_runs',job['renderer_exe'],job['renderer_exe'])

    def test_full_routes_and_full_text_delivery_to_both_roles(self):
        from skill_routes import ROUTES,configure
        skillroot=self.root/'custom-skill-root'
        for relative in {f for files in ROUTES.values() for f in files}:
            p=skillroot/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Reference '+relative)
        for profile in ROUTES:
            with self.subTest(profile=profile):
                job=configure(self.state['job'],skillroot,profile)
                a.write(self.root/'routed.json',job)
                run,state=a.start(self.root/'routed.json',self.root/'routed_runs',job['renderer_exe'],job['renderer_exe'])
                self.assertEqual(a.guidance_attachments(state,run),[])
                prompts=[]
                def turn(role,n,prompt,attachments):
                    prompts.append(role)
                    guidance=json.loads(prompt)['presentation_guidance']
                    self.assertEqual(len(guidance),len(ROUTES[profile]))
                    self.assertTrue(all(g['content'].startswith('Reference ') for g in guidance))
                    self.assertLessEqual(len(attachments),1)
                    if role=='A':return dict(source=SOURCE)
                    return dict(verdict='accept',vision_probe='ABCDEF',findings=[])
                with patch.object(a.Worker,'turn',side_effect=turn),patch.object(a.Worker,'native',side_effect=self.native_render),patch.object(a.secrets,'token_hex',return_value='abcdef'):
                    a.propose(state,run);a.resume(state,run,a.request_contract(state,run))
                self.assertEqual(prompts,['A','B'])
        missing=skillroot/'nature-figure/static/core/contract.md';missing.unlink()
        with self.assertRaisesRegex(ValueError,'missing'):configure(self.state['job'],skillroot,'civil-curves')

    def test_unverified_stdin_or_cleanup_never_retried(self):
        from author_role_retry import classify
        folder=self.root/'attempt';folder.mkdir()
        a.write(folder/'attempt_inputs.json',{})
        (folder/'request.stderr').write_text('HTTP 503 connection reset')
        for receipt in (dict(cleanupConfirmed=False,stdinRequired=False),
                        dict(cleanupConfirmed=True,stdinRequired=True,stdinComplete=False),
                        dict(cleanupConfirmed=True,stdinRequired=False,terminationRequested=True),
                        dict(cleanupConfirmed=True,stdinRequired=False,reason='timeout',exitCode=124)):
            a.write(folder/'request.native.json',receipt)
            self.assertFalse(classify(folder,RuntimeError('native'))[0])


if __name__=='__main__':unittest.main(verbosity=2)
