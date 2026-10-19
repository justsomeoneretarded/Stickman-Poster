"""A standalone short script built from the strongest generated story beats."""
import json
import math
import sys
import time
from pathlib import Path
from .writer import write_planned


def highlight_plan(project,target_seconds):
    scenes=project['scenes']
    desired=min(len(scenes),max(3,min(8,math.ceil(target_seconds/10))))
    # Preserve opening and payoff, then choose high-scored visual gags in story order.
    chosen={0,len(scenes)-1}
    ranked=sorted(range(1,len(scenes)-1),key=lambda i:(scenes[i].get('short_score',0)+
                  (3 if scenes[i].get('staging') in {'lift','fly','react','reveal'} else 0)),reverse=True)
    used={scenes[i].get('gag_id',i) for i in chosen}
    for i in ranked:
        group=scenes[i].get('gag_id')
        if group is None:group=i
        if group in used:continue
        chosen.add(i);used.add(group)
        if len(chosen)>=desired:break
    by_id={c['id']:c['voice'] for c in project['cast']}
    result=[]
    for i in sorted(chosen):
        s=scenes[i]
        result.append({'speaker':by_id[s['speaker']],'location':s['location'],
                       'staging':s['staging'],'shot':s.get('shot','medium'),'prop':s.get('prop','none'),
                       'purpose':s.get('purpose','')+' Source line: '+s['narration'],
                       'comic_role':'hook' if i==0 else 'payoff' if i==len(scenes)-1 else 'escalation',
                       'short_score':s.get('short_score',0),'source_scene_id':s['id']})
    return result


def write_short(project_path,request_path,out,model_dir):
    project=json.loads(Path(project_path).read_text());request=json.loads(Path(request_path).read_text())
    target=request.get('short_seconds',60)
    plan=highlight_plan(project,target)
    for i,voice in enumerate(request['voices']):plan[i]['speaker']=voice
    request={**request,'minutes':target/60,'tone':'description-driven','required_locations':[],
             'description':request['description']+' Create a STANDALONE punchy vertical short from the selected source beats. '
             'Rewrite dialogue to connect the selected scenes naturally; do not assume viewers saw the long version. '
             'Hook in the first sentence. Preserve the requested tone and ending; do not add jokes unless the description explicitly requests them. Avoid references to omitted scenes.'}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'highlight-selection.json').write_text(json.dumps({'target_seconds':target,
        'method':'outline highlight scores plus visual interest, preserving opening and payoff; dialogue rewritten for standalone continuity',
        'source_scene_ids':[s['source_scene_id'] for s in plan]},indent=2))
    write_planned(request,out,model_dir,time.perf_counter(),plan)


if __name__=='__main__':write_short(*sys.argv[1:])
