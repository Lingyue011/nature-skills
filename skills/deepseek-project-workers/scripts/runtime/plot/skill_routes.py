"""Task-specific skill selection; no model calls or execution of skill scripts."""
import argparse
import hashlib
import json
from pathlib import Path

CORE=['nature-figure/SKILL.md','nature-figure/manifest.yaml',
      'nature-figure/static/core/contract.md','nature-figure/static/core/stance.md']
PYTHON=CORE+['nature-figure/static/fragments/backend/python.md',
             'nature-figure/references/qa-contract.md']
CIVIL=PYTHON+['nature-figure/references/civil-engineering-profile.md']
PANELS=['nature-figure/references/multipanel-evidence-architecture.md']
ROUTES={
    'scientific-python':PYTHON,
    'civil-curves':CIVIL,
    'civil-panels':CIVIL+PANELS,
    'civil-image-plate':CIVIL+PANELS,
    'civil-paraview':CIVIL+['civil-paraview-figures/SKILL.md',
                          'civil-paraview-figures/references/paraview-recipes.md'],
    'editable-schematic':CORE+['nature-figure/references/vector-schematic-workflow.md',
                              'nature-figure/references/vector-schematic-style-rules.md'],
    'academic-diagram':['academic-plotting/SKILL.md'],
}


def configure(job,skillroot,profile):
    if profile not in ROUTES:raise ValueError('Unknown routed profile')
    paths=[(Path(skillroot)/p).resolve() for p in ROUTES[profile]]
    for p in paths:
        if not p.is_file():raise ValueError('Required skill resource missing: '+str(p))
    result=dict(job,figure_profile=profile,guidance_delivery='stdin',
                guidance_files=[str(p) for p in paths],
                approved_guidance_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                skill_routes_version=1)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--job',required=True)
    p.add_argument('--output',required=True);p.add_argument('--profile',required=True,choices=list(ROUTES))
    p.add_argument('--skill-root',default=str(Path.home()/'.codex/skills'));a=p.parse_args()
    out=Path(a.output)
    routed=configure(json.loads(Path(a.job).read_text(encoding='utf-8-sig')),a.skill_root,a.profile)
    with out.open('x',encoding='utf-8') as f:
        json.dump(routed,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status='routed_job_created',profile=a.profile,job=str(out))))
