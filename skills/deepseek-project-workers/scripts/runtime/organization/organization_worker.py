"""Bounded DS organization proposals; root-approved, journaled Windows file moves."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import sys
import time
from model_transport import Worker, read, write, sha, checked_file

HERE=Path(__file__).resolve().parent
RESERVED={'CON','PRN','AUX','NUL',*[f'{p}{n}' for p in ['COM','LPT'] for n in range(1,10)]}


def safe_path(root, relative):
    """Reject traversal, Windows aliases and reparse points before resolving paths."""
    if not isinstance(relative,str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Require a plain relative POSIX path')
    rel=PurePosixPath(relative)
    if rel.is_absolute() or str(rel)!=relative or any(x in ('.','..') for x in rel.parts):
        raise ValueError('Noncanonical or escaping path')
    if any(x.rstrip(' .')!=x or x.split('.')[0].upper() in RESERVED or any(ord(c)<32 or c in '<>"|?*' for c in x) for x in rel.parts):
        raise ValueError('Windows path alias/reserved character')
    root=Path(root).absolute()
    path=root.joinpath(*rel.parts)
    for item in [root,*root.parents,path,*list(path.parents)[:len(rel.parts)]]:
        if item.is_symlink() or getattr(item,'is_junction',lambda:False)():
            raise ValueError('Reparse paths are not supported')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path outside repository')
    return path


def is_under(path,prefix):
    p,q=path.casefold(),prefix.casefold().rstrip('/')
    return p==q or p.startswith(q+'/')


def inventory(job):
    root=Path(job['repository']).resolve()
    closure=checked_file(job['closure_review'])
    if sha(closure)!=job['closure_sha256']:
        raise ValueError('Root dependency-review changed')
    rows=[];seen=set()
    if not 1<=len(job['candidates'])<=200:
        raise ValueError('Only 1..200 explicit candidates per bounded job')
    for i,c in enumerate(job['candidates']):
        rel=c['path'];p=safe_path(root,rel)
        if rel.casefold() in seen or is_under(rel,'trash') or is_under(rel,'.git'):
            raise ValueError('Duplicate/trash/Git candidate')
        seen.add(rel.casefold())
        if not p.is_file() or p.stat().st_nlink!=1:
            raise ValueError('Only existing, non-hardlinked regular files are supported')
        protected=any(is_under(rel,x) for x in job['protected_paths'])
        allowed=c['eligible'] is True and not protected
        if p.stat().st_size>8*1024*1024:
            raise ValueError('Narrow this job: candidate exceeds 8 MiB')
        rows.append(dict(id=f'F{i+1:03}',path=rel,bytes=p.stat().st_size,sha256=sha(p),
                         eligible=allowed,root_note=c['note']))
    return dict(repository=str(root),closure_review=str(closure),closure_sha256=sha(closure),
                protected_paths=job['protected_paths'],entries=rows)


def decisions(answer,inv):
    rows=answer.get('entries')
    if not isinstance(rows,list) or len(rows)!=len(inv['entries']):
        raise ValueError('Classify every inventory item exactly once')
    allowed={r['id']:r for r in inv['entries']};seen=set();normalized=[]
    for row in rows:
        if set(row)!={'id','action','reason'} or row['id'] not in allowed or row['id'] in seen:
            raise ValueError('Unknown/duplicate entry or unapproved output fields')
        seen.add(row['id'])
        if row['action'] not in ('keep','move','hold') or not isinstance(row['reason'],str) or not 1<=len(row['reason'])<=700:
            raise ValueError('Invalid decision/reason')
        if row['action']=='move' and not allowed[row['id']]['eligible']:
            raise ValueError('Protected/unapproved file selected')
        normalized.append(dict(row))
    return sorted(normalized,key=lambda x:x['id'])


def plan(jobfile,runroot,pwsh,cli):
    job=read(jobfile)
    if type(job['roles']) is not int or job['roles'] not in (2,4) or not 30<=job['turn_seconds']<=600 or not 120<=job['wall_seconds']<=2400 or len(job['task'])>12000:
        raise ValueError('Invalid role count/budgets')
    root=Path(runroot).resolve();repo=Path(job['repository']).resolve()
    if root.is_relative_to(repo):
        raise ValueError('RunRoot must be outside the scientific repository')
    inv=inventory(job)
    root.mkdir(parents=True,exist_ok=True)
    run=root/(time.strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(4));run.mkdir()
    write(run/'job.json',job);write(run/'inventory.json',inv)
    worker=Worker(dict(max_rounds=2,turn_seconds=job['turn_seconds'],wall_seconds=job['wall_seconds'],
                       role_retries=job.get('role_retries',2),max_replacements=job.get('max_replacements',4)),run,pwsh,cli)
    closure=Path(job['closure_review']).read_text(encoding='utf-8-sig')
    if len(closure)>18000:raise ValueError('Narrow the root dependency context')
    common=dict(inventory=inv,root_dependency_facts=closure,task=job['task'],
                rules='No file access or tools. Classify provided facts; never authorize a scientific dependency retirement. Unknown dependencies => hold. No deletion, writes, builds, solves or push. Return bounded JSON.',
                scientific_scope='Root personally reviews scientific sources and dependency closure. Your dependency report is extraction/advice, not source/scientific acceptance.')
    result=dict(status='failed_pending_root_review',run=str(run),roles=job['roles'])
    try:
        a=worker.turn('A',1,json.dumps(dict(common,role='Inventory analyst',response_contract=dict(entries=[dict(id='F001 (all IDs)',action='keep|move|hold',reason='short evidence-based reason')],summary='short')),ensure_ascii=False))
        proposed=decisions(a,inv)
        contract=dict(verdict='accept|revise',blocking_ids='list of inventory IDs',findings='list of short concrete concerns')
        b=worker.turn('B',1,json.dumps(dict(common,role='Dependency reviewer',candidate=proposed,response_contract=contract),ensure_ascii=False))
        for response in [b]:validate_review(response,inv)
        if job['roles']==4:
            # Independent C sees source facts/inventory, not A/B recommendations.
            c=worker.turn('C',1,json.dumps(dict(common,role='Independent preservation counterexample reviewer',
                    focus='Find old-looking but active files, dynamic imports, evidence binding and duplicate-vs-dependency confusion.',response_contract=contract),ensure_ascii=False))
            validate_review(c,inv)
            d=worker.turn('D',1,json.dumps(dict(common,role='Integrator',candidate=proposed,dependency_review=b,
                independent_review=c,response_contract=dict(entries=[dict(id='every inventory ID',action='keep|move|hold',reason='resolve reviewer evidence')],summary='short unresolved limits')),ensure_ascii=False))
            final=decisions(d,inv)
            blockers=set(b['blocking_ids'])|set(c['blocking_ids'])
            # A disagreement can only reduce automatic move scope. Root can reopen
            # separately with new evidence; the integrator cannot override blockers.
            if b['verdict']=='revise' and not b['blocking_ids'] or c['verdict']=='revise' and not c['blocking_ids']:
                blockers|={r['id'] for r in inv['entries']}
            final=[dict(r,action='hold',reason=r['reason']+' [review blocker: Root decision required]') if r['id'] in blockers and r['action']=='move' else r for r in final]
            a_moves={r['id'] for r in proposed if r['action']=='move'}
            final=[dict(r,action='hold',reason=r['reason']+' [not in reviewed A move scope]') if r['action']=='move' and r['id'] not in a_moves else r for r in final]
        else:
            final=proposed
            if b['verdict']=='revise' or b['blocking_ids']:
                blockers=set(b['blocking_ids']) or {r['id'] for r in inv['entries']}
                final=[dict(r,action='hold') if r['id'] in blockers and r['action']=='move' else r for r in final]
        byid={r['id']:r for r in inv['entries']}
        selected=[byid[r['id']] for r in final if r['action']=='move']
        output=dict(status='proposed_pending_root_review',repository=inv['repository'],
                    inventory_sha256=sha(run/'inventory.json'),closure_review=inv['closure_review'],
                    closure_sha256=inv['closure_sha256'],destination='trash/ds_organization_'+run.name,
                    protected_paths=inv['protected_paths'],decisions=final,files=selected)
        write(run/'plan.json',output)
        if inventory(job)!=inv:raise ValueError('Scope changed during model review')
        sessions=[read(p) for p in sorted(run.glob('01_*/receipt.json'))]
        if len(sessions)!=job['roles'] or len({s['sessionId'] for s in sessions})!=job['roles']:
            raise ValueError('Role sessions not independent')
        result.update(status='proposed_pending_root_review',plan=str(run/'plan.json'),plan_sha256=sha(run/'plan.json'),
                      replacements_used=getattr(worker,'replacements',0),
                      proposed_files=len(selected),sessions=[s['sessionId'] for s in sessions])
    except Exception as e:result['error']=f'{type(e).__name__}: {e}'
    write(run/'result.json',result)
    return result


def validate_review(response,inv):
    if set(response)!={'verdict','blocking_ids','findings'} or response['verdict'] not in ('accept','revise'):
        raise ValueError('Invalid reviewer protocol')
    if not isinstance(response['blocking_ids'],list) or not set(response['blocking_ids'])<={r['id'] for r in inv['entries']}:
        raise ValueError('Invalid blocking IDs')
    if not isinstance(response['findings'],list) or any(not isinstance(x,str) or len(x)>1200 for x in response['findings']):
        raise ValueError('Invalid reviewer findings')


def journal(path,row):
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(time=time.time(),**row),ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())


def preflight(planfile,approvalfile):
    p=read(planfile);a=read(approvalfile)
    if a.get('status')!='root_approved_exact_move' or a.get('plan_sha256')!=sha(planfile):
        raise ValueError('Missing/mismatched Root approval')
    if a.get('approved_ids')!=[r['id'] for r in p['files']] or not a.get('reason'):
        raise ValueError('Approval must identify the exact selected IDs and reason')
    if sha(p['closure_review'])!=p['closure_sha256']:
        raise ValueError('Root dependency facts changed')
    invfile=Path(planfile).parent/'inventory.json';inv=read(invfile)
    if sha(invfile)!=p['inventory_sha256']:raise ValueError('Inventory changed')
    expected={r['id']:r for r in inv['entries']}
    if len({r['id'] for r in p['files']})!=len(p['files']):raise ValueError('Duplicate file operation')
    root=Path(p['repository']).resolve();rows=[]
    if not p['destination'].startswith('trash/ds_organization_') or len(PurePosixPath(p['destination']).parts)!=2:
        raise ValueError('Destination must be one dedicated trash directory')
    dest=safe_path(root,p['destination'])
    if dest.exists():raise ValueError('Destination exists; no overwrite/resume')
    if shutil.disk_usage(root).free<20*1024**3:raise ValueError('20 GiB disk reserve')
    for row in p['files']:
        if row!=expected.get(row['id']) or row['eligible'] is not True or any(is_under(row['path'],x) for x in p['protected_paths']):
            raise ValueError('File is outside approved eligible inventory')
        if is_under(row['path'],'trash') or is_under(row['path'],'.git'):raise ValueError('Source is protected')
        src=safe_path(root,row['path']);dst=safe_path(root,p['destination']+'/'+row['path'])
        if not src.is_file() or src.stat().st_nlink!=1 or sha(src)!=row['sha256'] or src.stat().st_size!=row['bytes']:
            raise ValueError('Source changed since review')
        rows.append((src,dst,row))
    # Protected witnesses are bounded exact inputs, not an all-project hash audit.
    for row in inv['entries']:
        if not row['eligible'] and sha(safe_path(root,row['path']))!=row['sha256']:
            raise ValueError('Protected witness changed')
    return p,rows


def apply(planfile,approvalfile,dry_run=False):
    p,rows=preflight(planfile,approvalfile)
    if dry_run:return dict(status='dry_run_passed',files=len(rows),bytes=sum(r['bytes'] for _,_,r in rows),destination=p['destination'])
    if os.name!='nt':raise ValueError('Real moves require Windows no-replace rename semantics')
    record=Path(planfile).parent/'execution'
    record.mkdir()  # exclusive; failed/partial jobs cannot restart automatically
    log=record/'journal.jsonl';done=[]
    result=dict(status='failed_pending_root_review',moved=done,plan_sha256=sha(planfile),approval_sha256=sha(approvalfile))
    try:
        for src,dst,row in rows:
            # Check again at the mutation boundary. No overwrite, shell or deletion.
            safe_path(Path(p['repository']),p['destination']+'/'+row['path'])
            if sha(src)!=row['sha256'] or dst.exists():raise ValueError('Changed source or occupied destination')
            dst.parent.mkdir(parents=True,exist_ok=True)
            journal(log,dict(event='intent',source=str(src),destination=str(dst),**row))
            src.rename(dst)
            if src.exists() or sha(dst)!=row['sha256']:raise ValueError('Post-move integrity failure')
            done.append(dict(source=str(src),destination=str(dst),**row))
            journal(log,dict(event='moved',**done[-1]))
        inv=read(Path(planfile).parent/'inventory.json')
        for row in inv['entries']:
            if not row['eligible'] and sha(safe_path(p['repository'],row['path']))!=row['sha256']:
                raise ValueError('Protected witness changed after move')
        result.update(status='moved_pending_root_review',bytes=sum(r['bytes'] for r in done))
    except Exception as e:result['error']=f'{type(e).__name__}: {e}'
    write(record/'result.json',result)
    return result


def rollback(planfile):
    p=read(planfile);record=Path(planfile).parent/'execution';result=read(record/'result.json')
    if result['status']!='moved_pending_root_review' or result['plan_sha256']!=sha(planfile):
        raise ValueError('Only a complete unchanged move can be explicitly rolled back')
    if (record/'rollback.json').exists():raise ValueError('Rollback already attempted')
    rows=[]
    if [{k:r[k] for k in ('id','path','bytes','sha256','eligible','root_note')} for r in result['moved']]!=p['files']:
        raise ValueError('Execution receipt does not match the approved plan')
    for row in result['moved']:
        src=safe_path(p['repository'],row['path']);dst=safe_path(p['repository'],p['destination']+'/'+row['path'])
        if src.exists() or not dst.is_file() or sha(dst)!=row['sha256']:raise ValueError('Rollback collision/change')
        rows.append((src,dst,row))
    outcome=dict(status='rollback_failed_pending_root_review',restored=[])
    write(record/'rollback.json',outcome)
    try:
        for src,dst,row in reversed(rows):
            journal(record/'journal.jsonl',dict(event='rollback_intent',**row))
            dst.rename(src)
            if sha(src)!=row['sha256']:raise ValueError('Restore integrity failure')
            outcome['restored'].append(row['id'])
            journal(record/'journal.jsonl',dict(event='restored',id=row['id']))
        outcome['status']='rolled_back_pending_root_review'
    except Exception as e:outcome['error']=str(e)
    write(record/'rollback.json',outcome)
    return outcome


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['plan','dry-run','apply','rollback'])
    parser.add_argument('--job');parser.add_argument('--plan');parser.add_argument('--approval')
    parser.add_argument('--run-root',default=str(HERE/'runs'))
    parser.add_argument('--pwsh',default=shutil.which('pwsh'))
    parser.add_argument('--cli',default=os.path.expandvars('%APPDATA%/npm/node_modules/@opencode/cli/bin/opencode.exe'))
    a=parser.parse_args()
    try:
        if a.mode=='plan':out=plan(a.job,a.run_root,a.pwsh,a.cli)
        elif a.mode=='rollback':out=rollback(a.plan)
        else:out=apply(a.plan,a.approval,a.mode=='dry-run')
        print(json.dumps(out,ensure_ascii=False));sys.exit(0 if out['status'] in ('proposed_pending_root_review','dry_run_passed','moved_pending_root_review','rolled_back_pending_root_review') else 2)
    except Exception as e:
        print(json.dumps(dict(status='blocked_pending_root_review',error=str(e)),ensure_ascii=False));sys.exit(2)
