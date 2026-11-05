"""Role-local upstream recovery. Never retries file mutation or acceptance gates."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path,row):
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(time=time.time(),**row),ensure_ascii=False)+'\n')
        stream.flush();os.fsync(stream.fileno())


def incomplete(text):
    text=text.strip()
    if not text.startswith(('{','[')):return False
    try:json.loads(text);return False
    except json.JSONDecodeError as e:
        return ('Unterminated' in e.msg or e.pos>=len(text)-2 or
                (text[-1:] not in ('}',']') and e.msg in ('Expecting value',"Expecting ',' delimiter")))


def classify(folder,error):
    """Conservative evidence classifier: unsafe/unknown errors cannot auto-retry."""
    evidence=folder/'attempt_inputs.json'
    if isinstance(error,subprocess.TimeoutExpired):return False,'outer_supervisor_timeout_cleanup_unverified'
    if not (folder/'request.native.json').exists():return False,'native_completion_unverified'
    for stem in ('request','session'):
        native=folder/(stem+'.native.json')
        if native.exists():
            receipt=load(native)
            # Kill(true)+WaitForExit proves direct exit, not complete descendant
            # cleanup. No automatic replacement after forced termination.
            if receipt.get('reason')=='timeout' or receipt.get('terminationRequested'):
                return False,'forced_termination_descendants_unverified'
            if receipt.get('cleanupConfirmed') is not True:
                return False,'owned_cleanup_unverified'
            if receipt.get('stdinRequired') and receipt.get('stdinComplete') is not True:
                return False,'stdin_delivery_unverified'
    if not evidence.exists():return False,'no_request_input_snapshot'
    try:
        if any(not Path(p).is_file() or digest(p)!=h for p,h in load(evidence).items()):
            return False,'request_inputs_changed'
    except (OSError,ValueError):return False,'request_inputs_unverifiable'
    events=[];truncated=False
    stream=folder/'request.stdout'
    if stream.exists():
        lines=[x for x in stream.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
        for index,line in enumerate(lines):
            try:events.append(json.loads(line))
            except json.JSONDecodeError:
                if index!=len(lines)-1:return False,'invalid_middle_of_stream'
                if re.search(r'"type"\s*:\s*"tool_use"',line):return False,'partial_tool_event'
                truncated=incomplete(line)
    if any(e.get('type')=='tool_use' for e in events):return False,'unexpected_tool_event'
    messages=[]
    session_file=folder/'session.stdout'
    if session_file.exists():
        try:
            session=load(session_file)
            expected=dict(id='deepseek-v4.1-flash',providerID='opencode-go',variant='max')
            models=[session.get('info',{}).get('model')]
            models += [m.get('model') for m in session.get('messages',[]) if m.get('type')=='assistant']
            if any(m and m!=expected for m in models):return False,'unexpected_model'
            info=session.get('info',{})
            if info.get('error'):messages.append(str(info['error']))
        except json.JSONDecodeError:
            if not incomplete(session_file.read_text(encoding='utf-8-sig')):
                return False,'invalid_session_export'
            truncated=True
    errors=[e for e in events if e.get('type')=='error']
    messages += [json.dumps(e,ensure_ascii=False) for e in errors]
    for stem in ['request','session']:
        stderr=folder/(stem+'.stderr')
        if stderr.exists():messages.append(stderr.read_text(encoding='utf-8-sig')[-6000:])
    signals='\n'.join(messages).lower()
    # Authentication, exhausted entitlement and permission rejection need action;
    # they must not be disguised as network instability by an accompanying EOF.
    if re.search(r'\b(401|402|403)\b|unauthori[sz]ed|authentication|api.?key|quota.?exhaust|insufficient.?quota|permission.?denied',signals):
        return False,'auth_permission_or_quota'
    fatal=('Unapproved model','Session/outcome mismatch','Attachment/config changed',
           'output limit','dispatch cap','wall limit','oversized')
    if any(s.lower() in str(error).lower() for s in fatal):
        # A failed outcome with an explicit transport error can be replaced;
        # identity mismatch and all other gates remain terminal.
        if 'session/outcome mismatch' not in str(error).lower():return False,'verification_or_budget_gate'
        try:
            if load(session_file).get('info',{}).get('outcome')=='succeeded':return False,'session_identity_mismatch'
        except (OSError,ValueError):return False,'unverifiable_session_identity'
    if re.search(r'\b(408|429|500|502|503|504)\b|econnreset|etimedout|econnrefused|unexpected eof|stream.{0,35}(closed|reset|truncat)|connection.{0,25}(reset|closed)|socket hang up',signals):
        return True,'upstream_transport'
    for stem in ['request','session']:
        native=folder/(stem+'.native.json')
        if native.exists():
            receipt=load(native)
            if receipt.get('exitCode')==124 and receipt.get('reason')=='timeout':
                return True,'owned_native_request_timeout'
    texts=[e.get('part',{}).get('text','') for e in events if e.get('type')=='text']
    if truncated or texts and incomplete(texts[-1]):return True,'truncated_upstream_json'
    return False,'non_transient_or_unclassified'


def run_role(worker,role,round_n,prompt,attachments):
    retries=worker.job.get('role_retries',2)
    max_replacements=worker.job.get('max_replacements',4)
    if type(retries)is not int or not 0<=retries<=3 or type(max_replacements)is not int or not 0<=max_replacements<=8:
        raise ValueError('Invalid role replacement budget')
    worker.calls+=1
    if worker.calls>2*worker.job['max_rounds']:raise RuntimeError('Logical role dispatch cap')
    if not hasattr(worker,'replacements'):worker.replacements=0
    ledger=worker.run/'role_attempts.jsonl'
    for attempt in range(1,retries+2):
        folder=worker.run/(f'{round_n:02}_{role}'+(f'_retry{attempt:02}' if attempt>1 else ''))
        record(ledger,dict(event='start',role=role,round=round_n,attempt=attempt,folder=str(folder)))
        try:
            answer=worker._turn_once(role,round_n,prompt,attachments,attempt=attempt)
            record(ledger,dict(event='succeeded',role=role,round=round_n,attempt=attempt,
                              replacements_used=worker.replacements))
            return answer
        except Exception as error:
            transient,reason=classify(folder,error)
            allowed=(transient and attempt<=retries and worker.replacements<max_replacements and
                     worker.job['wall_seconds']-(time.monotonic()-worker.start)>=5)
            row=dict(event='failed',role=role,round=round_n,attempt=attempt,reason=reason,
                     transient=transient,replacement_scheduled=allowed,error=f'{type(error).__name__}: {error}')
            record(ledger,row)
            if folder.exists():
                (folder/'attempt_failure.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
            if not allowed:raise
            worker.replacements+=1
            # Bounded backoff; same prompt/inputs/model, fresh independent session.
            remaining=worker.job['wall_seconds']-(time.monotonic()-worker.start)
            time.sleep(min(2*attempt,max(0,remaining-5)))
