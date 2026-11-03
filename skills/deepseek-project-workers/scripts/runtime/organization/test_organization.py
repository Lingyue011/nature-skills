"""Bounded safety checks with temporary fixtures; no DS calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import organization_worker as o


class OrganizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'old').mkdir();(self.root/'old/cache.bin').write_bytes(b'cache')
        (self.root/'active.py').write_text('active source',encoding='utf-8')
        self.closure=self.root/'closure.json';o.write(self.closure,dict(status='test_only'))
        self.job=dict(repository=str(self.root),closure_review=str(self.closure),closure_sha256=o.sha(self.closure),
            protected_paths=['active.py'],candidates=[dict(path='old/cache.bin',eligible=True,note='fixture'),dict(path='active.py',eligible=False,note='protected')])
        self.inv=o.inventory(self.job)
        self.run=self.root/'evidence';self.run.mkdir();o.write(self.run/'inventory.json',self.inv)
        self.plan=self.run/'plan.json'
        o.write(self.plan,dict(repository=str(self.root),inventory_sha256=o.sha(self.run/'inventory.json'),closure_review=str(self.closure),closure_sha256=o.sha(self.closure),destination='trash/ds_organization_test',protected_paths=['active.py'],files=[self.inv['entries'][0]]))
        self.approval=self.run/'approval.json';self.approve()

    def approve(self):
        o.write(self.approval,dict(status='root_approved_exact_move',plan_sha256=o.sha(self.plan),approved_ids=['F001'],reason='test fixture only'))

    def test_path_guards(self):
        for rel in ['../outside','/root/file','C:/x','old\\x','old/../x','old//x','.git/../x','old/NUL.txt','old/x.','old/x:stream']:
            with self.subTest(rel=rel),self.assertRaises(ValueError):o.safe_path(self.root,rel)

    def test_reject_protected_and_duplicate_model_choices(self):
        for entries in [[dict(id='F001',action='move',reason='ok'),dict(id='F002',action='move',reason='bad')],
                        [dict(id='F001',action='keep',reason='ok')]*2]:
            with self.assertRaises(ValueError):o.decisions(dict(entries=entries),self.inv)

    def test_requires_exact_approval(self):
        a=o.read(self.approval);a['plan_sha256']='bad';o.write(self.approval,a)
        with self.assertRaises(ValueError):o.apply(self.plan,self.approval,True)

    def test_changed_source_blocks_entire_batch(self):
        (self.root/'old/cache.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError):o.apply(self.plan,self.approval,True)
        self.assertFalse((self.root/'trash').exists())

    def test_existing_target_and_link_guard(self):
        (self.root/'trash/ds_organization_test').mkdir(parents=True)
        with self.assertRaises(ValueError):o.apply(self.plan,self.approval,True)
        import os
        os.link(self.root/'old/cache.bin',self.root/'alias.bin')
        with self.assertRaises(ValueError):o.inventory(self.job)

    def test_dry_run_move_and_explicit_rollback(self):
        before=o.sha(self.root/'active.py')
        self.assertEqual(o.apply(self.plan,self.approval,True)['status'],'dry_run_passed')
        result=o.apply(self.plan,self.approval)
        self.assertEqual(result['status'],'moved_pending_root_review')
        self.assertFalse((self.root/'old/cache.bin').exists())
        self.assertEqual(o.sha(self.root/'active.py'),before)
        self.assertEqual(o.rollback(self.plan)['status'],'rolled_back_pending_root_review')
        self.assertEqual((self.root/'old/cache.bin').read_bytes(),b'cache')

    def test_rollback_collision_preserves_both(self):
        o.apply(self.plan,self.approval)
        (self.root/'old/cache.bin').write_bytes(b'new source')
        with self.assertRaises(ValueError):o.rollback(self.plan)
        self.assertEqual((self.root/'old/cache.bin').read_bytes(),b'new source')
        self.assertTrue((self.root/'trash/ds_organization_test/old/cache.bin').exists())

    def test_changed_protected_witness(self):
        (self.root/'active.py').write_text('changed source',encoding='utf-8')
        with self.assertRaises(ValueError):o.apply(self.plan,self.approval,True)

    def test_wrong_reviewer_ids(self):
        with self.assertRaises(ValueError):o.validate_review(dict(verdict='accept',blocking_ids=['outside'],findings=[]),self.inv)

    def test_four_roles_independent_counterreview_and_blocker(self):
        outside=tempfile.TemporaryDirectory();self.addCleanup(outside.cleanup)
        job=dict(self.job,roles=4,turn_seconds=30,wall_seconds=120,task='test')
        jf=self.root/'job.json';o.write(jf,job)
        author=dict(entries=[dict(id='F001',action='move',reason='cache'),dict(id='F002',action='keep',reason='source')],summary='test')
        seen=[]
        def turn(worker,role,n,prompt,attachments=()):
            seen.append(role);payload=json.loads(prompt)
            if role=='C':
                self.assertNotIn('candidate',payload);self.assertNotIn('dependency_review',payload)
            folder=worker.run/f'01_{role}';folder.mkdir()
            o.write(folder/'receipt.json',dict(sessionId=f'ses_test_{role}'))
            if role in ('A','D'):return author
            return dict(verdict='revise' if role=='B' else 'accept',blocking_ids=['F001'] if role=='B' else [],findings=[])
        with patch.object(o.Worker,'turn',new=turn):
            result=o.plan(jf,Path(outside.name)/'runs','unused','unused')
        self.assertEqual(seen,['A','B','C','D'])
        self.assertEqual(result['status'],'proposed_pending_root_review')
        self.assertEqual(result['proposed_files'],0)


if __name__=='__main__':unittest.main(verbosity=2)
