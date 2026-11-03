"""Root-approved frozen-data renderer. Only approved presentation fields vary."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--layout',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    l=json.loads(a.layout.read_text(encoding='utf-8'))
    def load(name,x,y,xf,yf):
        with (a.inputs/name).open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        return np.array([[float(r[x])*xf,float(r[y])*yf] for r in rows])
    test=load('displacement_Test.csv','time_min','V6_mm',1,1)
    fe=load('displacement_FE.csv','time_s','fire_increment_m',1/60,1000)
    assert test.shape==(82,2) and fe.shape==(392,2)
    assert np.isfinite(test).all() and np.isfinite(fe).all()
    plt.rcParams.update({'font.family':'Times New Roman','mathtext.fontset':'stix',
                         'path.simplify':False,'axes.unicode_minus':True})
    fig=plt.figure(figsize=(85/25.4,75/25.4),dpi=300)
    ax=fig.add_axes([l['left'],l['bottom'],l['right']-l['left'],l['top']-l['bottom']])
    tline,=ax.plot(test[:,0],test[:,1],color='black',lw=1.25,label='Test')
    fline,=ax.plot(fe[:,0],fe[:,1],color='#94263A',lw=1.3,ls=(0,(8,4)),label='FE')
    ax.set(xlim=(0,180),ylim=(-180,5),xticks=[0,30,60,90,120,150,180],yticks=[0,-40,-80,-120,-160])
    ax.set_xlabel(r'Time, $t$ (min)',fontsize=l['axis_font'],labelpad=l['xlabel_pad'])
    ax.set_ylabel(r'Displacement, $w$ (mm)',fontsize=l['axis_font'],labelpad=l['ylabel_pad'])
    ax.tick_params(direction='in',top=True,right=True,labelsize=l['tick_font'],length=3,width=.8,pad=3)
    ax.grid(True,color='#AAAAAA',lw=.45,ls=(0,(2,2)))
    legend=ax.legend(loc=l['legend_loc'],frameon=False,fontsize=l['legend_font'],handlelength=2.6,
                     borderpad=.25,labelspacing=.35)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    bounds=fig.bbox
    artists=[ax.xaxis.label,ax.yaxis.label,*ax.get_xticklabels(),*ax.get_yticklabels(),*legend.get_texts()]
    clipped=[]
    for text in artists:
        b=text.get_window_extent(renderer)
        if b.x0<2 or b.y0<2 or b.x1>bounds.x1-2 or b.y1>bounds.y1-2:
            clipped.append(text.get_text())
    lb=legend.get_window_extent(renderer).padded(2)
    curve_overlap=[]
    for name,xy in [('Test',test),('FE',fe)]:
        pixels=ax.transData.transform(xy)
        # Segment-box overlap, including when both endpoints lie outside.
        for x,y in zip(pixels[:-1],pixels[1:]):
            from matplotlib.path import Path as MPath
            if MPath([x,y]).intersects_bbox(lb,filled=False):
                curve_overlap.append(name); break
    vertices_ok=(np.array_equal(tline.get_xydata(),test) and np.array_equal(fline.get_xydata(),fe))
    font_min=min(l['axis_font'],l['tick_font'],l['legend_font'])
    issues=[]
    if clipped: issues.append('Clipped text: '+repr(clipped))
    if curve_overlap: issues.append('Legend overlaps curves: '+repr(curve_overlap))
    if font_min<10: issues.append('All text must be at least 10 pt at final 85 mm width')
    if not vertices_ok: issues.append('Curve vertices changed')
    if l['right']-l['left']<.65 or l['top']-l['bottom']<.62:
        issues.append('Plot area too small; reduce excessive margins')
    fig.savefig(a.output/'figure.png',dpi=600,facecolor='white')
    fig.savefig(a.output/'preview.png',dpi=300,facecolor='white')
    qa=dict(passed=not issues,issues=issues,rows={'Test':len(test),'FE':len(fe)},
            vertices_exact=vertices_ok,minimum_final_font_pt=font_min,
            input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.inputs.iterdir()},
            definition='Original Test; FE fire increment in mm; all vertices retained; no fitting.',
            canvas_mm=[85,75],dpi=600)
    (a.output/'qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    plt.close(fig)


if __name__=='__main__':
    main()
