"""Deterministic silent-heartbeat semantics; no model calls or long sleeps."""
import json,tempfile,unittest
from pathlib import Path
from author_progress import ProgressMonitor

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.stem=Path(self.tmp.name)/'request';self.now=0
        self.monitor=ProgressMonitor(self.stem,'model_request',2400,clock=lambda:self.now)
    def append(self,kind,text=''):
        with Path(str(self.stem)+'.stdout').open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(type=kind,sessionID='ses_fixture',part={'text':text}))+'\n')
    def test_start_and_liveness_not_remote_progress(self):
        self.append('step_start');r=self.monitor.snapshot()
        self.assertEqual(r['status'],'waiting_no_visible_model_progress')
        self.assertIsNone(r['last_visible_model_output_age_seconds'])
        self.assertTrue(r['native_call_pending'])
    def test_actual_output_observed_without_persisting_content(self):
        self.append('reasoning','PRIVATE_REASONING_NOT_FOR_HEARTBEAT')
        r=self.monitor.snapshot();self.assertEqual(r['status'],'visible_model_output_recent')
        saved=Path(str(self.stem)+'.progress.json').read_text()
        self.assertNotIn('PRIVATE_REASONING_NOT_FOR_HEARTBEAT',saved)
        self.now=61;self.assertEqual(self.monitor.snapshot()['status'],'waiting_no_visible_model_progress')
    def test_600_second_silent_heartbeat_and_terminal(self):
        self.monitor.snapshot();p=Path(str(self.stem)+'.heartbeats.jsonl');self.assertFalse(p.exists())
        self.now=599;self.monitor.snapshot();self.assertFalse(p.exists())
        self.now=600;self.monitor.snapshot();self.assertEqual(len(p.read_text().splitlines()),1)
        self.now=1200;self.monitor.snapshot();self.assertEqual(len(p.read_text().splitlines()),2)
        r=self.monitor.finish('request_timeout_stopped');self.assertFalse(r['native_call_pending'])
        self.assertEqual(len(p.read_text().splitlines()),3)
    def test_partial_event_then_complete_and_nonmodel_operation(self):
        p=Path(str(self.stem)+'.stdout');p.write_text('{"type":"text","part":{"text":"ok"}}',encoding='utf-8')
        self.assertEqual(self.monitor.snapshot()['event_counts'].get('text',0),0)
        with p.open('a') as f:f.write('\n')
        self.assertEqual(self.monitor.snapshot()['event_counts']['text'],1)
        other=ProgressMonitor(Path(self.tmp.name)/'render','render',90)
        self.assertEqual(other.snapshot()['status'],'local_operation_pending')
    def test_observer_write_failure_does_not_break_execution(self):
        from unittest.mock import patch
        with patch.object(self.monitor,'snapshot',side_effect=OSError('fixture')):
            self.monitor.__enter__();r=self.monitor.finish('native_completed_pending_verification')
        self.assertEqual(r['observer_error'],'OSError')

    def test_root_reader_does_not_trust_stale_pending_heartbeat(self):
        from read_author_progress import summarise
        root=self.stem.parent
        (root/'state.json').write_text(json.dumps({'status':'author_running'}))
        self.monitor.snapshot()
        live=json.loads(Path(str(self.stem)+'.progress.json').read_text())
        from datetime import datetime
        updated=datetime.fromisoformat(live['updated_utc'].replace('Z','+00:00')).timestamp()
        r=summarise(root,now=updated+60)
        self.assertEqual(r['observer_status'],'stale')
        self.assertEqual(r['model_progress'],'unknown')
        self.assertEqual(r['root_action'],'check_controller_and_native_receipt_do_not_assume_alive')

    def test_root_acceptance_requires_matching_source_and_image(self):
        from read_author_progress import summarise
        import hashlib
        root=self.stem.parent;(root/'state.json').write_text(json.dumps({'status':'candidate_ready_pending_root_review','round':1}))
        (root/'01_candidate.py').write_text('source');(root/'01_render').mkdir();(root/'01_render/figure.png').write_bytes(b'fixture')
        record={'accepted':True,'source_sha256':hashlib.sha256(b'source').hexdigest(),'figure_sha256':hashlib.sha256(b'fixture').hexdigest()}
        (root/'root_final_acceptance.json').write_text(json.dumps(record))
        self.assertEqual(summarise(root)['root_action'],'none_root_acceptance_recorded')
        (root/'01_candidate.py').write_text('changed')
        self.assertNotEqual(summarise(root)['root_action'],'none_root_acceptance_recorded')

if __name__=='__main__':unittest.main(verbosity=2)
