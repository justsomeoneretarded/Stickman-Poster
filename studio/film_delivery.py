"""Production documents and planned subtitle tracks for primarily visual films.

All cue times refer to the planned timeline, never an unrendered video's measured
or word-aligned timeline. No silent action is invented as spoken narration.
"""
import json
import math
from pathlib import Path

CAST_CHOICES={
    'Maya (female)':['female'], 'Leo (Kit Laser)':['male1'], 'Max (Warguy)':['male2'],
    'Maya + Leo':['female','male1'], 'Maya + Max':['female','male2'],
    'Leo + Max':['male1','male2'], 'Maya + Leo + Max':['female','male1','male2']}


def select_cast(value):
    if isinstance(value,str) and value in CAST_CHOICES:return CAST_CHOICES[value][:]
    selected=value.split(',') if isinstance(value,str) else value
    if not selected or len(set(selected))!=len(selected) or any(v not in ('female','male1','male2') for v in selected):
        raise ValueError('Select one, two or three approved characters')
    return list(selected)


def delivery_schema(props,scene,string):
    cue_props={'kind':{'type':'string','enum':['ambience','foley','speech','music','silence']},
               'start_seconds':{'type':'number','minimum':0},'end_seconds':{'type':'number','exclusiveMinimum':0},
               'detail':string,'reason':string,'caption':string,'speaker':string,'text':string,'offscreen':{'type':'boolean'}}
    scene['properties'].update({
        'actors':{'type':'array','minItems':1,'items':{'type':'string','enum':['Maya','Leo','Max']}},
        'emotion_start':string,'emotion_end':string,'story_beat':string,
        'cues':{'type':'array','items':{'type':'object','properties':cue_props,'required':list(cue_props),'additionalProperties':False}},
        'screen_text':{'type':'array','items':{'type':'object','properties':{
            'start_seconds':{'type':'number','minimum':0},'end_seconds':{'type':'number','exclusiveMinimum':0},
            'text':string,'purpose':string},'required':['start_seconds','end_seconds','text','purpose'],'additionalProperties':False}}})
    scene['required']+=['actors','emotion_start','emotion_end','story_beat','cues','screen_text']
    arc={name:string for name in ('story_type','desire','hook','exposition','inciting_change','escalation','pinch_point','all_is_lost','turning_point','climax','falling_action','resolution')}
    props['story_arc']={'type':'object','properties':arc,'required':list(arc),'additionalProperties':False}
    thumb={name:string for name in ('hook_text','emotional_promise','composition','image_prompt','source_scene_id')}
    props['thumbnails']={'type':'array','minItems':3,'maxItems':3,'items':{'type':'object','properties':thumb,'required':list(thumb),'additionalProperties':False}}


def _span(cue,seconds,label):
    a,b=cue['start_seconds'],cue['end_seconds']
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (a,b)) or not 0<=a<b<=seconds+1e-7:
        raise ValueError(f'{label} must have finite ordered times inside its scene')
    if b>seconds:cue['end_seconds']=seconds


def validate_delivery(film,request,cast):
    visible={cast[v] for v in request.get('characters',list(cast))}
    voices={cast[v] for v in request['voices']}
    for s in film['scenes']:
        if 'actors' in s and (not s['actors'] or any(a not in visible for a in s['actors'])):
            raise ValueError('Visible scene actors must use the selected characters')
        for c in s.get('cues',[]):
            _span(c,s['seconds'],'Sound cue')
            if not c['reason'].strip():raise ValueError('Sound cues need a story reason')
            if c['kind']=='speech':
                if c['speaker'] not in voices or not c['text'].strip():raise ValueError('Speech cues must use selected voices and actual dialogue')
                if not c['offscreen'] and c['speaker'] not in s.get('actors',list(visible)):
                    raise ValueError('An on-screen speaker must be visible in that scene')
            elif c['text'].strip() or c['speaker'].strip():raise ValueError('Only speech cues may contain spoken text or a speaker')
            if c['kind']=='silence' and c['caption'].strip():raise ValueError('Silence is not a sound subtitle')
        if 'cues' in s:
            spoken=[(c['speaker'],c['text']) for c in s['cues'] if c['kind']=='speech']
            dialogue=[(c['character'],c['text']) for c in s['dialogue']]
            if sorted(spoken)!=sorted(dialogue):raise ValueError('Dialogue and speech cues must match exactly')
        for c in s.get('screen_text',[]):_span(c,s['seconds'],'Screen text')
    if 'thumbnails' in film:
        ids={s['id'] for s in film['scenes']}
        if len(film['thumbnails'])!=3:raise ValueError('Provide exactly three thumbnail options')
        if len({t['image_prompt'].strip() for t in film['thumbnails']})!=3:raise ValueError('Thumbnail options need distinct compositions')
        for t in film['thumbnails']:
            if t['source_scene_id'] not in ids:raise ValueError('Thumbnail must reference an actual story scene')
            if not t['image_prompt'].strip():raise ValueError('Thumbnail needs an image prompt')


def stamp(seconds):
    ms=round(seconds*1000);hh,ms=divmod(ms,3600000);mm,ms=divmod(ms,60000);ss,ms=divmod(ms,1000)
    return f'{hh:02}:{mm:02}:{ss:02},{ms:03}'


def srt(entries):
    return '\n\n'.join(f'{i}\n{stamp(a)} --> {stamp(b)}\n'+text.replace('-->','→').strip()
                       for i,(a,b,text) in enumerate(sorted(entries,key=lambda e:(e[0],e[1])),1))+'\n' if entries else ''


def write_delivery(film,request,out):
    out=Path(out);subs=[];screen=[];cues=[];timeline=[];offset=0
    for scene in film['scenes']:
        for c in scene.get('cues',[]):
            item={**c,'scene_id':scene['id'],'timeline_start':offset+c['start_seconds'],'timeline_end':offset+c['end_seconds']}
            cues.append(item)
            caption=c['text'] if c['kind']=='speech' else c['caption']
            if caption.strip() and c['kind']!='silence':subs.append((item['timeline_start'],item['timeline_end'],caption))
        for c in scene.get('screen_text',[]):screen.append((offset+c['start_seconds'],offset+c['end_seconds'],c['text']))
        timeline.append({'id':scene['id'],'start_seconds':offset,'end_seconds':offset+scene['seconds'],
                         'actors':scene.get('actors',[]),'action':scene['action'],'camera':scene['camera'],
                         'emotion_start':scene.get('emotion_start',''),'emotion_end':scene.get('emotion_end',''),
                         'story_beat':scene.get('story_beat',''),'screen_text':scene.get('screen_text',[])})
        offset+=scene['seconds']
    (out/'subtitles.srt').write_text(srt(subs))
    (out/'screen-text.srt').write_text(srt(screen))
    for name,data in [('sound-plan.json',cues),('shot-plan.json',timeline),('story-arc.json',film.get('story_arc',{})),('thumbnail-briefs.json',film.get('thumbnails',[]))]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n')
    thumbs=film.get('thumbnails',[])
    thumb_dir=out/'thumbnails';thumb_dir.mkdir(exist_ok=True)
    for i,t in enumerate(thumbs,1):
        (thumb_dir/f'option-{i}-prompt.txt').write_text(t['image_prompt']+'\n\nExact suggested headline: '+t['hook_text']+'\n')
    (out/'subtitle-notes.txt').write_text('Planned timeline only. These are not measured or word-aligned subtitles for a finished video.\n'
        'subtitles.srt: actual speech and deliberately selected meaningful sound captions.\n'
        'screen-text.srt: separately planned sparse visual text; not automatically burned in.\n'
        'Empty tracks are valid for silence/no screen text. Retiming is required after picture and audio lock.\n')
    (out/'publishing-description.txt').write_text(film['publishing_description'].strip()+'\n')
    arc='\n'.join(f'{k.replace("_"," ").title()}: {v}' for k,v in film.get('story_arc',{}).items())
    (out/'description.txt').write_text(film['publishing_description'].strip()+'\n\nKEYWORDS\n'+', '.join(film['keywords'])+
         '\n\nSTORY\n'+film['story']+'\n\nSTORY STRUCTURE\n'+arc+'\n\nVISUAL SCREENPLAY (not voiceover)\n'+(out/'script.md').read_text())
    (out/'delivery-status.json').write_text(json.dumps({'stage':'production_plan','video_rendered':False,
       'thumbnail_images_rendered':0,'thumbnail_briefs':len(thumbs),'subtitle_timing':'planned; retime after final render',
       'missing':['Full-film layered animation renderer','Contextual audio synthesis and mix','Three final thumbnail images unless image backend is configured']},indent=2)+'\n')
