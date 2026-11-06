"""One compact read-only status for Root; no model calls or process actions."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import time
import hashlib

def root_accepted(run,state):
    try:
        r=json.loads((run/'root_final_acceptance.json').read_text(encoding='utf-8-sig'))
        n=state['round'];code=run/('%02d_candidate.py'%n);png=run/('%02d_render'%n)/'figure.png'
        return (r.get('accepted') is True and
            r.get('source_sha256')==hashlib.sha256(code.read_bytes()).hexdigest() and
            r.get('figure_sha256')==hashlib.sha256(png.read_bytes()).hexdigest())
    except (OSError,ValueError,KeyError):return False

def summarise(run,now=None,stale_after=30):
    run=Path(run);now=time.time() if now is None else now
    state=json.loads((run/'state.json').read_text(encoding='utf-8-sig'))
    result=dict(run=run.name,worker_state=state['status'],observer_status='not_available',
                model_progress='unknown',root_action='continue_within_existing_budget')
    if root_accepted(run,state):
        result.update(root_action='none_root_acceptance_recorded',model_progress='root_accepted_source_and_image')
        return result
    if state['status']=='pending_code_review':
        result.update(root_action='review_exact_source_before_execution',model_progress='source_returned')
    elif state['status'] not in ('created','author_running','render_running','review_running'):
        result['root_action']='inspect_terminal_result'
    paths=list(run.rglob('*.progress.json'))
    if not paths:return result
    p=max(paths,key=lambda x:x.stat().st_mtime)
    live=json.loads(p.read_text(encoding='utf-8-sig'))
    try:age=max(0,now-datetime.fromisoformat(live['updated_utc'].replace('Z','+00:00')).timestamp())
    except (KeyError,ValueError,TypeError):age=None
    stale=age is None or age>stale_after
    result.update(operation=live.get('operation'),attempt_directory=live.get('attempt_directory'),
        elapsed_seconds=live.get('elapsed_seconds'),request_limit_seconds=live.get('request_limit_seconds'),
        observer_age_seconds=round(age,3) if age is not None else None,
        observer_status='stale' if stale else 'fresh',observer_warning=live.get('observer_error'),
        stream_status=live.get('status'),event_counts=live.get('event_counts'),
        last_visible_output_age_seconds=live.get('last_visible_model_output_age_seconds'))
    if result['model_progress']!='source_returned' and not stale:
        result['model_progress']=live.get('status')
    receipt=p.with_name(p.name.removesuffix('.progress.json')+'.native.json')
    if receipt.exists():
        r=json.loads(receipt.read_text(encoding='utf-8-sig'))
        result['native_receipt']=dict(exit_code=r.get('exitCode'),reason=r.get('reason'),
            cleanup_confirmed=r.get('cleanupConfirmed'),active_processes=r.get('activeProcessesAfterCleanup'))
    elif stale:
        result['root_action']='check_controller_and_native_receipt_do_not_assume_alive'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
    print(json.dumps(summarise(a.run),ensure_ascii=False))
