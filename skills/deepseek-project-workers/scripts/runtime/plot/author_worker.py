"""DS-owned presentation code, persistent Root release gates, independent image review.

This is a reviewed-code execution workflow, NOT an OS sandbox. Root must read
the actual source and its effects before signing an exact execution approval.
"""
import argparse
import ast
from contextlib import contextmanager
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

from plot_worker import Worker as BaseWorker, checked_file, read, write, sha, MODEL, HERE
from skill_routes import ROUTES
from author_role_retry import run_role
from author_progress import ProgressMonitor

VERSION = 'author-v1.4'


class Worker(BaseWorker):
    """Same fixed-model/receipt/retry transport; long prompts go through stdin.

    OpenCode v2 --file is one string: only the actual image uses that flag.
    Guidance stays full text in prompt.txt and request.stdin.txt, never a second
    attachment. No arbitrary command parsing or new model tools are introduced.
    """
    def turn(self,role,round_n,prompt,attachments=()):
        return run_role(self,role,round_n,prompt,attachments)

    def native(self,exe,args,cwd,stem,seconds):
        remaining=self.job['wall_seconds']-(time.monotonic()-self.start)
        if remaining<5:raise TimeoutError('Whole-job wall limit')
        args=list(map(str,args));inputfile=None
        operation='model_request' if args and args[0]=='run' else ('session_export' if args[:2]==['session','export'] else 'render')
        if args and args[0]=='run':
            if args.count('--file')>1:raise ValueError('Only one image attachment supported')
            prompt=args.pop()
            if len(prompt)>250000:raise ValueError('stdin prompt limit')
            inputfile=Path(str(stem)+'.stdin.txt');inputfile.write_text(prompt,encoding='utf-8')
        spec=dict(exe=str(exe),arguments=args,cwd=str(cwd),
            stdout=str(stem)+'.stdout',stderr=str(stem)+'.stderr',
            receipt=str(stem)+'.native.json',timeout=min(seconds,remaining),
            outputBytes=8*1024*1024,inputFile=str(inputfile) if inputfile else None)
        write(str(stem)+'.spec.json',spec)
        monitor=ProgressMonitor(stem,operation,spec['timeout'])
        monitor.__enter__()
        try:
            proc=subprocess.run([self.pwsh,'-NoProfile','-File',str(HERE/'author_job_process.ps1'),
                '-SpecFile',str(stem)+'.spec.json'],capture_output=True,timeout=spec['timeout']+35)
            receipt=read(spec['receipt'])
        except Exception:
            monitor.finish('native_call_exception_cleanup_requires_review')
            raise
        monitor.finish('request_timeout_stopped' if receipt.get('reason')=='timeout' else
            ('native_failed' if proc.returncode or receipt['exitCode'] or receipt.get('reason') else 'native_completed_pending_verification'))
        if proc.returncode or receipt['exitCode'] or receipt.get('reason'):
            raise RuntimeError('Native failure: '+str(receipt))
        if sum(p.stat().st_size for p in self.run.rglob('*') if p.is_file())>64*1024*1024:
            raise RuntimeError('Whole-job output limit')
        return Path(spec['stdout']).read_text(encoding='utf-8-sig')


def bounded(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('Invalid '+name)


def safe_dir(path):
    path = Path(path).absolute()
    for parent in [path, *path.parents]:
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('Linked directory rejected')
    return path


@contextmanager
def lock(run):
    token = run/'author.lock'
    with token.open('x') as f:
        f.write(str(__import__('os').getpid()))
    try:
        yield
    finally:
        token.unlink()


def controller_hashes():
    files = [Path(__file__), HERE/'skill_routes.py', HERE/'author_job_process.ps1',HERE/'author_role_retry.py',HERE/'author_progress.py',
             HERE/'plot_worker.py', HERE/'role_retry.py', HERE/'native.ps1']
    return {str(p.resolve()): sha(p) for p in files}


def check_immutable(state):
    for section in ('originals', 'frozen', 'controllers', 'executables'):
        for p, digest in state[section].items():
            if sha(checked_file(p)) != digest:
                raise ValueError(section+' changed: '+p)
    jobpath=next(p for p in state['frozen'] if Path(p).name=='job.json')
    for name in ('inputs','guidance'):
        inputdir=safe_dir(Path(jobpath).parent/name)
        expected={p for p in state['frozen'] if Path(p).parent==inputdir}
        actual={str(checked_file(p)) for p in inputdir.iterdir()}
        if actual!=expected:
            raise ValueError(name+' directory membership changed')
    if {state['pwsh'],state['cli'],state['job']['renderer_exe']}!=set(state['executables']):
        raise ValueError('Executable paths changed')
    if read(jobpath)!=state['job']:
        raise ValueError('Persisted job differs from frozen job')
    if time.time()-state['started_epoch'] >= state['job']['wall_seconds']:
        raise TimeoutError('Whole-job wall limit including Root review pauses')


def stage_summary(state,run):
    """Separate observed stages; none of these is physical-model validation."""
    def artifact(path):
        try:
            value=read(path)
            return value if isinstance(value,dict) else {}
        except (OSError,ValueError):return {}
    n=state['round'];code=run/('%02d_candidate.py'%n);out=run/('%02d_render'%n)
    qa=artifact(out/'qa.json');vision=artifact(out/'vision_verification.json')
    feedback=state.get('feedback',{});feedback=feedback if isinstance(feedback,dict) else {}
    approval=artifact(run/('%02d_root_approval.json'%n))
    native=artifact(run/('%02d_render_process.native.json'%n))
    result=dict(round=n,worker_state=state['status'],source_returned=code.is_file(),
        source_released=bool(code.is_file() and approval.get('source_sha256')==sha(code)),
        render_exit_code=native.get('exitCode'),machine_checks_passed=qa.get('passed'),
        independent_image_delivery_passed=vision.get('passed'),
        independent_review=feedback.get('verdict') if vision.get('passed') is True and state.get('feedback_round')==n else 'not_completed',
        root_acceptance='not_recorded',role_usage={})
    for role in ('A','B'):
        receipts=sorted(run.glob('%02d_%s*/receipt.json'%(n,role)),key=lambda p:p.stat().st_mtime)
        if receipts:
            r=artifact(receipts[-1]);result['role_usage'][role]=dict(
                model=r.get('model'),tokens=r.get('tokens'),request_seconds=r.get('native',{}).get('seconds'))
    final=artifact(run/'root_final_acceptance.json')
    png=out/'figure.png'
    if (final.get('accepted') is True and code.is_file() and png.is_file()
        and final.get('source_sha256')==sha(code) and final.get('figure_sha256')==sha(png)):
        result['root_acceptance']='recorded_matching_source_and_image'
    return result


def save(run, state):
    # Keep a durable state at every boundary; never auto-resume an interrupted effect.
    tmp = run/'state.tmp'
    write(tmp, state)
    tmp.replace(run/'state.json')
    write(run/'result.json', dict(status=state['status'], run=str(run),
        round=state['round'], model=MODEL, review='pending_root_review',
        calls=state['calls'], replacements=state['replacements'], error=state.get('error')))
    try:summary=stage_summary(state,run)
    except Exception as error:summary={'evidence_observation_error':type(error).__name__}
    write(run/'stage_summary.json',summary)


def worker(state, run):
    w = Worker(state['job'], run, state['pwsh'], state['cli'])
    w.start = time.monotonic()-(time.time()-state['started_epoch'])
    w.calls, w.replacements = state['calls'], state['replacements']
    return w


def request_contract(state, run):
    code = run/('%02d_candidate.py'%state['round'])
    return dict(status='root_approved_exact_render', version=VERSION,
        job_sha256=sha(run/'job.json'), run_id=run.name, round=state['round'],
        source_sha256=sha(code), input_hashes=state['frozen'],
        renderer_exe=state['job']['renderer_exe'],
        renderer_sha256=state['job']['renderer_sha256'], controllers=state['controllers'],
        executables=state['executables'])


def guided_prompt(state,run,prompt):
    # External DS cannot read Codex's skills automatically. Send approved text
    # explicitly to BOTH roles; frozen files and prompt.txt preserve provenance.
    prompt['figure_profile']=state['job'].get('figure_profile','generic')
    prompt['presentation_guidance']=[dict(name=p.name,sha256=sha(p),
        content=p.read_text(encoding='utf-8-sig')) for p in sorted((run/'guidance').iterdir())]
    prompt['guidance_scope']='Apply presentation guidance to this project contract. '
    prompt['guidance_scope']+='Project units, axes and scientific definitions take precedence over example-specific defaults. '
    prompt['guidance_scope']+='Do not claim to have loaded helpers or run checks merely because guidance mentions them.'
    if 'data_brief' in state['job']:
        prompt['root_data_brief']=state['job']['data_brief']
    role=prompt.get('role','')
    if role.startswith('A:'):
        scope=('AUTHOR ONLY: write the complete presentation source. Runtime checks and image inspection '
               'occur after Root releases the source; do not execute them or claim their results now. '
               'Use the supplied schema/brief to write file-reading code; the catalog is not file-content access. '
               'The program must load the frozen files, not substitute preview rows or hardcode example values.')
    elif role.startswith('B:'):
        scope=('REVIEWER ONLY: inspect the attached actual image and supplied source, identify concrete '
               'visual/data-preservation issues and return the requested verdict/probe. Do not write a '
               'replacement program or repeat the author workflow. Machine QA alone is not visual acceptance.')
    else:scope='Apply only the guidance relevant to the current assigned phase.'
    prompt['current_phase_contract']=scope+' The shared task describes the overall goal; it does not reassign your role.'
    encoded=json.dumps(prompt,ensure_ascii=False)
    limit=245000 if state['job'].get('guidance_delivery','inline')=='stdin' else 28000
    if len(encoded.encode('utf-16-le'))//2>limit:
        raise ValueError('Combined prompt exceeds selected prompt budget; narrow task/guidance/source')
    return encoded


def guidance_attachments(state,run):
    return []  # Skills are full prompt text; --file is reserved for one image.


def propose(state, run):
    check_immutable(state)
    state['status']='author_running';save(run,state)
    w=worker(state,run)
    previous=run/('%02d_candidate.py'%(state['round']-1))
    catalog=[dict(name=p.name,bytes=p.stat().st_size) for p in (run/'inputs').iterdir()]
    prompt=dict(role='A: presentation program author', task=state['job']['task'],
        immutable_inputs=catalog, contract=state['job']['input_contract'],
        previous_source=previous.read_text(encoding='utf-8') if previous.exists() else None,
        review_feedback=state.get('feedback'),
        instructions='Write the complete Python presentation program yourself. Do not invoke tools. '
        'Accept --inputs DIRECTORY and --output NEW_DIRECTORY. Read only listed files under inputs. '
        'Write figure.png, preview.png and qa.json (passed boolean plus meaningful checks) only under output. '
        'No shell, subprocess, network, solver, pip, credentials or reading unrelated files. '
        'Only presentation logic; do not change scientific values/definitions. Use installed libraries. '
        'The code will be paused for Root review before execution. Keep code concise (<11000 chars).',
        response_contract=dict(source='complete Python source string, no markdown fences',summary='brief'))
    attachments=[]
    if state['round']>1:
        attachments=[run/('%02d_render'%(state['round']-1))/'preview.png']
    elif state['job'].get('author_preview'):
        image=run/'inputs'/state['job']['author_preview']
        if image.name!=state['job']['author_preview'] or str(image) not in state['frozen']:
            raise ValueError('author_preview must be an approved input basename')
        attachments=[image]
    try:
        answer=w.turn('A',state['round'],guided_prompt(state,run,prompt),attachments+guidance_attachments(state,run))
    finally:
        state['calls'],state['replacements']=w.calls,w.replacements
    source=answer.get('source')
    if not isinstance(source,str) or not 1<len(source)<=32000:
        raise ValueError('Missing/oversized presentation source')
    ast.parse(source)  # Syntax check only; not a safety or scientific approval.
    code=run/('%02d_candidate.py'%state['round']);code.write_text(source,encoding='utf-8')
    write(run/('%02d_author_handoff.json'%state['round']),answer)
    state['status']='pending_code_review'
    write(run/'approval_template.json',request_contract(state,run))
    check_immutable(state);save(run,state)


def validate_approval(state,run,approval):
    check_immutable(state)
    if state['status']!='pending_code_review':
        raise ValueError('Resume requires pending_code_review; no automatic replay')
    expected=request_contract(state,run)
    if approval != expected:
        raise ValueError('Approval does not match exact code/job/inputs/runtime/controller')
    code=run/('%02d_candidate.py'%state['round'])
    if sha(checked_file(state['job']['renderer_exe']))!=state['job']['renderer_sha256']:
        raise ValueError('Renderer runtime changed')
    return code


def review_image(state,run,w,out,source,qa):
    from PIL import Image,ImageDraw,ImageFont
    token=secrets.token_hex(3).upper()
    with Image.open(checked_file(out/'preview.png')) as im:
        im.load()
        if im.width>5000 or im.height>5000:raise ValueError('Preview too large')
        sheet=Image.new('RGB',(max(im.width,550),im.height+130),'white');sheet.paste(im,(0,0))
    draw=ImageDraw.Draw(sheet)
    draw.text((20,sheet.height-100),token,fill='black',font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',48))
    sheet.save(out/'review_sheet.png')
    # Token deliberately absent from prompt and all text files until B responds.
    prompt=dict(role='B: independent actual-image reviewer',task=state['job']['task'],
        scientific_contract=state['job']['input_contract'],presentation_source=source,machine_qa=qa,
        instructions='Inspect the actual image, source, label meaning, data preservation, bounds, '
        'legibility and design. Transcribe the six hexadecimal characters at the bottom of the image. '
        'Do not infer image quality from QA alone. Return concise actionable findings for A.',
        response_contract=dict(verdict='accept or revise',vision_probe='six characters',findings='list',summary='brief'))
    b=w.turn('B',state['round'],guided_prompt(state,run,prompt),[out/'review_sheet.png',*guidance_attachments(state,run)])
    write(out/'vision_verification.json',dict(expected=token,returned=b.get('vision_probe'),passed=b.get('vision_probe')==token))
    if b.get('vision_probe')!=token:raise ValueError('Image-delivery probe failed')
    if b.get('verdict') not in ('accept','revise') or not isinstance(b.get('findings'),list):
        raise ValueError('Malformed complete B handoff')
    return b


def resume(state,run,approval):
    code=validate_approval(state,run,approval)
    source=code.read_text(encoding='utf-8');codehash=sha(code)
    out=run/('%02d_render'%state['round'])
    if out.exists():raise ValueError('Render directory exists; never rerun an effect')
    state['status']='render_running';save(run,state)
    write(run/('%02d_root_approval.json'%state['round']),approval)
    w=worker(state,run)
    # Reviewed source owns presentation. Do not interpret generated command strings.
    w.native(state['job']['renderer_exe'],[str(code),'--inputs',str(run/'inputs'),'--output',str(out)],
        run,run/('%02d_render_process'%state['round']),state['job']['render_seconds'])
    check_immutable(state)
    if sha(code)!=codehash:raise ValueError('Candidate source changed during render')
    checked_file(out/'figure.png');checked_file(out/'preview.png')
    qa=read(checked_file(out/'qa.json'))
    if type(qa.get('passed')) is not bool:raise ValueError('QA requires boolean passed')
    state['status']='review_running';save(run,state)
    try:
        feedback=review_image(state,run,w,out,source,qa)
    finally:
        state['calls'],state['replacements']=w.calls,w.replacements
    check_immutable(state)
    state['feedback']=feedback;state['feedback_round']=state['round'];state['candidate']=str(out/'figure.png')
    if feedback['verdict']=='accept' and qa['passed']:
        state['status']='candidate_ready_pending_root_review';save(run,state)
    elif state['round']>=state['job']['max_rounds']:
        state['status']='round_limit_pending_root_review';save(run,state)
    else:
        state['round']+=1;propose(state,run)


def start(jobfile,runroot,pwsh,cli):
    job=read(checked_file(jobfile))
    # Defaults for new drawing jobs only; explicit diagnostic/older caps stay explicit.
    job.setdefault('turn_seconds',2400)
    job.setdefault('wall_seconds',10800)
    for key,lo,hi in [('max_rounds',1,3),('turn_seconds',30,2400),('wall_seconds',120,14400),('render_seconds',10,180)]:
        bounded(job[key],lo,hi,key)
    bounded(job.get('role_retries',2),0,2,'role_retries')
    bounded(job.get('max_replacements',4),0,4,'max_replacements')
    if not isinstance(job['task'],str) or len(job['task'])>12000:raise ValueError('Task size')
    if not isinstance(job['input_contract'],str) or len(job['input_contract'])>12000:raise ValueError('Contract size')
    if not 1<=len(job['inputs'])<=12:raise ValueError('Input count')
    inputs=[checked_file(p) for p in job['inputs']]
    if 'data_brief' in job:
        brief=job['data_brief']
        if not isinstance(brief,dict) or len(json.dumps(brief,ensure_ascii=False))>12000:
            raise ValueError('data_brief must be a bounded Root-owned object')
        files=brief.get('files',[])
        if not isinstance(files,list) or any(not isinstance(f,dict) or not isinstance(f.get('name'),str)
            or f['name'] not in {p.name for p in inputs} for f in files):
            raise ValueError('data_brief references an unapproved input')
    if len({p.name for p in inputs})!=len(inputs):raise ValueError('Duplicate input basenames')
    if sum(p.stat().st_size for p in inputs)>24*1024*1024:raise ValueError('Input total exceeds 24 MiB')
    exe=checked_file(job['renderer_exe'])
    if exe.suffix.lower()!='.exe' or sha(exe)!=job['renderer_sha256']:raise ValueError('Renderer identity')
    pwsh=str(checked_file(pwsh));cli=str(checked_file(cli))
    executables={str(p):sha(p) for p in (Path(pwsh),Path(cli),exe)}
    originals={str(p):sha(p) for p in inputs}
    if originals!=job['approved_sha256']:raise ValueError('Root-approved input hashes mismatch')
    guidance=[checked_file(p) for p in job.get('guidance_files',[])]
    delivery=job.get('guidance_delivery','inline')
    if delivery not in ('inline','stdin'):raise ValueError('Unknown guidance delivery')
    if len(guidance)>16 or sum(p.stat().st_size for p in guidance)>(196608 if delivery=='stdin' else 24000):
        raise ValueError('Guidance exceeds selected delivery budget')
    guidance_hashes={str(p):sha(p) for p in guidance}
    if guidance_hashes!=job.get('approved_guidance_sha256',{}):
        raise ValueError('Root-approved guidance hashes mismatch')
    profile=job.get('figure_profile','generic')
    if profile not in ('generic',*ROUTES):raise ValueError('Unknown figure_profile')
    for relative in ROUTES.get(profile,[]):
        suffix=Path(relative).parts
        if not any(p.parts[-len(suffix):]==suffix for p in guidance):
            raise ValueError('Routed skill resources incomplete: '+relative)
    originals.update(guidance_hashes)
    parent=safe_dir(runroot);parent.mkdir(parents=True,exist_ok=True)
    run=parent/(time.strftime('%Y%m%d-%H%M%S')+'-author-'+secrets.token_hex(4));run.mkdir()
    (run/'inputs').mkdir()
    (run/'guidance').mkdir()
    for p in inputs:shutil.copyfile(p,run/'inputs'/p.name)
    for i,p in enumerate(guidance):shutil.copyfile(p,run/'guidance'/('%02d-'%i+p.name))
    write(run/'job.json',job)
    frozen={str(p):sha(p) for p in (run/'inputs').iterdir()};frozen[str(run/'job.json')]=sha(run/'job.json')
    frozen.update({str(p):sha(p) for p in (run/'guidance').iterdir()})
    state=dict(version=VERSION,status='created',job=job,started_epoch=time.time(),round=1,
        calls=0,replacements=0,originals=originals,frozen=frozen,controllers=controller_hashes(),
        pwsh=pwsh,cli=cli,executables=executables)
    save(run,state)
    return run,state


def command(args):
    if args.mode=='start':
        run,state=start(args.job,args.run_root,args.pwsh,args.cli)
    else:
        run=safe_dir(args.run)
    with lock(run):
        if args.mode=='resume':state=read(checked_file(run/'state.json'))
        if args.mode=='resume' and state['status']!='pending_code_review':
            raise ValueError('Resume requires pending_code_review; preserved existing state')
        try:
            if args.mode=='start':propose(state,run)
            else:resume(state,run,read(checked_file(args.approval)))
        except Exception as e:
            state['status']='failed_pending_root_review';state['error']=type(e).__name__+': '+str(e);save(run,state)
    return read(run/'result.json')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['start','resume'])
    p.add_argument('--job');p.add_argument('--run');p.add_argument('--approval')
    p.add_argument('--run-root',default=str(HERE/'author_runs'))
    p.add_argument('--pwsh',required=True);p.add_argument('--cli',required=True)
    try:
        result=command(p.parse_args());print(json.dumps(result,ensure_ascii=False))
        sys.exit(0 if result['status'] in ('pending_code_review','candidate_ready_pending_root_review') else 2)
    except Exception as e:
        print(json.dumps(dict(status='blocked_pending_root_review',error=str(e))));sys.exit(2)
