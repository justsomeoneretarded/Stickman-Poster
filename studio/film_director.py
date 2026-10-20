"""Generate an executable visual film, with symbolic model choices and app-owned timing."""
import copy
import hashlib
import json
from pathlib import Path
from .film_concept import CAST,write_package
from .local_llm import LocalWriter
from .writer import MODEL_ID,MODEL_REVISION

SETTINGS=['cafe','street','bedroom','park','bus_stop','studio','classroom']
ACTIONS=['sit','stand','walk','run','reach','sip','draw','phone','offer','receive','look_away','slump','open_door','pick_up','put_down','listen']
EMOTIONS=['neutral','sad','hopeful','anxious','happy','bored','angry','tired']
PROPS=['none','cup','phone','sketchbook','paper','bag']
ASSETS=['room','rain','wind','steps','phone_vibration','door_bell','cup_set','chair_scrape','car_horn','coin_drop','paper_rustle','pencil','speech','silence']
PACING={'brief':1,'normal':1.35,'linger':1.75}


def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
def enum(values):return {'type':'string','enum':values}
STR={'type':'string'}

def outline_schema():
    scene=obj({'id':STR,'location':enum(SETTINGS),'beat':STR,'action':STR,'change':STR})
    return obj({'logline':STR,'story':STR,'ending':STR,'scenes':{'type':'array','minItems':6,'maxItems':10,'items':scene},
                'publishing_description':STR,'keywords':{'type':'array','minItems':5,'maxItems':12,'items':STR}})


def shot_schema(request):
    actors=[CAST[v] for v in request['characters']];voices=[CAST[v] for v in request['voices']]
    actor=obj({'character':enum(actors),'action':enum(ACTIONS),'emotion_start':enum(EMOTIONS),'emotion_end':enum(EMOTIONS),
               'prop':enum(PROPS),'posture':enum(['standing','seated']),'from':enum(['left','center','right']),'to':enum(['left','center','right']),
               'look':enum(['left','right','down','forward'])})
    cue=obj({'asset':enum([a for a in ASSETS if a!='speech' or voices]),'at':enum(['begin','middle','end']),
             'speaker':enum(['']+voices),'text':STR,'caption':STR,'offscreen':{'type':'boolean'},'reason':STR})
    shot=obj({'setting':enum(SETTINGS),'actors':{'type':'array','minItems':1,'maxItems':len(actors),'items':actor},
              'framing':enum(['wide','medium','closeup','insert']),'focus':enum(actors),
              'motion':enum(['hold','push','pull','pan']),'pacing':enum(list(PACING)),
              'score':enum(['quiet','warm','tense','silent']),'description':STR,'camera_reason':STR,'screen_text':STR,
              'cues':{'type':'array','maxItems':4,'items':cue}})
    return obj({'shots':{'type':'array','minItems':3,'maxItems':5,'items':shot}})


def _cached(writer,folder,name,prompt,user,schema,tokens,signature,validator):
    path=folder/(name+'.json');key=hashlib.sha256((signature+name+json.dumps(user,sort_keys=True)).encode()).hexdigest()
    if path.exists():
        value=json.loads(path.read_text())
        if value.get('key')==key:return validator(value['result'])
    feedback=''
    for attempt in range(3):
        print(f'{name}: generation {attempt+1}/3',flush=True)
        try:
            value=json.loads(writer.complete([{'role':'system','content':prompt},{'role':'user','content':json.dumps(user)+feedback}],schema,tokens))
            value=validator(value);path.write_text(json.dumps({'key':key,'result':value},indent=2)+'\n');return value
        except (ValueError,KeyError,TypeError) as exc:
            print(f'{name}: repair {exc}',flush=True);feedback='\nReturn complete concise JSON. Repair: '+str(exc)
            if attempt==2:raise


def validate_shots(value,request):
    if not 3<=len(value['shots'])<=5:raise ValueError('Use 3–5 directed shots per sequence')
    visible={CAST[v] for v in request['characters']};voices={CAST[v] for v in request['voices']}
    for shot in value['shots']:
        names=[a['character'] for a in shot['actors']]
        if len(names)!=len(set(names)) or not set(names)<=visible:raise ValueError('Use distinct selected actors')
        if shot['focus'] not in names:raise ValueError('Camera focus must appear in this shot')
        positions=[a['from'] for a in shot['actors']]
        if len(positions)!=len(set(positions)):raise ValueError('Give actors distinct starting positions')
        for actor in shot['actors']:
            if actor['action'] not in ACTIONS or actor['prop'] not in PROPS:raise ValueError('Unsupported actor action/prop')
            if actor['action'] in ('walk','run') and actor['from']==actor['to']:raise ValueError('Walking/running must actually change position')
            if actor['action']=='sip' and actor['prop']!='cup':raise ValueError('Sipping needs a cup')
            if actor['action']=='phone' and actor['prop']!='phone':raise ValueError('Phone acting needs a phone')
            if actor['action']=='draw' and actor['prop'] not in ('paper','sketchbook'):raise ValueError('Drawing needs paper or a sketchbook')
        if any(a['action'] in ('offer','receive') for a in shot['actors']):
            roles={a['action'] for a in shot['actors']}
            pair=[a for a in shot['actors'] if a['action'] in ('offer','receive')]
            if len(pair)!=2 or {a['action'] for a in pair}!={'offer','receive'}:raise ValueError('A handoff needs exactly one offering and one receiving actor in the same shot')
            if pair[0]['prop']=='none' or pair[0]['prop']!=pair[1]['prop']:raise ValueError('Both handoff actors need the same actual prop')
        for cue in shot['cues']:
            if cue['asset']=='speech':
                if cue['speaker'] not in voices or not cue['text'].strip():raise ValueError('Speech must use a selected voice and actual words')
                if not cue['offscreen'] and cue['speaker'] not in names:raise ValueError('Onscreen speech requires a visible actor')
            elif cue['speaker'] or cue['text']:raise ValueError('Non-speech sounds have empty speaker and text')
    return value


def compile_film(outline,directed,request):
    shots=[copy.deepcopy(s) for group in directed for s in group['shots']]
    target=request['minutes']*60;weight=sum(PACING[s['pacing']] for s in shots)
    sequences=[];cursor=0
    for sequence,group in zip(outline['scenes'],directed):
        compiled=[];dialogue=[];cues=[];texts=[];seconds=0
        for shot in group['shots']:
            shot=copy.deepcopy(shot);shot['id']=f'shot-{cursor+1:03}';cursor+=1
            shot['seconds']=max(1,round(target*PACING[shot['pacing']]/weight*request['fps']))/request['fps']
            shot['start_in_sequence']=seconds
            for cue in shot['cues']:
                at={'begin':.08,'middle':.45,'end':.75}[cue['at']]*shot['seconds']
                length=min(shot['seconds']-at, max(1.2,len(cue['text'].split())/2.2+.4) if cue['asset']=='speech' else 1.8)
                cue['start_seconds']=at;cue['end_seconds']=at+length
                kind='speech' if cue['asset']=='speech' else 'silence' if cue['asset']=='silence' else 'ambience' if cue['asset'] in ('rain','room','wind') else 'foley'
                cues.append({'kind':kind,'start_seconds':seconds+at,'end_seconds':seconds+at+length,'detail':cue['asset'],
                             'reason':cue['reason'],'caption':cue['caption'] if kind!='silence' else '',
                             'speaker':cue['speaker'],'text':cue['text'],'offscreen':cue['offscreen']})
                if kind=='speech':dialogue.append({'character':cue['speaker'],'text':cue['text']})
            if shot['screen_text']:texts.append({'start_seconds':seconds+.2,'end_seconds':seconds+shot['seconds']-.2,'text':shot['screen_text'],'purpose':shot['description']})
            seconds+=shot['seconds'];compiled.append(shot)
        actors=list(dict.fromkeys(a['character'] for s in compiled for a in s['actors']))
        sequences.append({'id':sequence['id'],'seconds':seconds,'location':sequence['location'],'dramatic_change':sequence['change'],
            'action':sequence['action'],'camera':'\n'.join(s['framing']+': '+s['camera_reason'] for s in compiled),'dialogue':dialogue,
            'sound':'Contextual cues selected by the director; see sound-plan.json.','music':'Original sparse motif, directed shot by shot.',
            'essential_text':'','actors':actors,'emotion_start':compiled[0]['actors'][0]['emotion_start'],
            'emotion_end':compiled[-1]['actors'][0]['emotion_end'],'story_beat':sequence['beat'],'cues':cues,'screen_text':texts,'shots':compiled})
    # The short is a separately generated complete story below, never an arbitrary source crop.
    return {'logline':outline['logline'],'story':outline['story'],'publishing_description':outline['publishing_description'],
            'keywords':outline['keywords'],'thumbnail_text':'','scenes':sequences,
            'short_edit':{'scene_ids':[s['id'] for s in sequences],'story':outline['story'],'ending':outline['ending']}}


def develop(request,out,model_dir,short=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);draft=out/'director';draft.mkdir(exist_ok=True)
    signature=hashlib.sha256(json.dumps([request,MODEL_ID,MODEL_REVISION,'executable-film-v1'],sort_keys=True).encode()+Path(__file__).read_bytes()).hexdigest()
    cast=', '.join(CAST[v] for v in request['characters'])
    with LocalWriter(model_dir,draft,context=8192) as writer:
        prompt=('Write an original mostly silent emotional animated film from a title and two-line brief. No voiceover, moral lecture, compulsory joke or forced redemption. '
                'Use a strong visual hook, desire, escalating concrete events, pressure, a genuine setback, a motivated choice/climax and earned aftermath. '
                'Show meaning through actions, props, expressions and contrasts; never explain the lesson. The description controls the ending. '
                'Only these approved characters appear: '+cast+'. Maya has chestnut wavy hair/scarf/taupe knit/full trousers; Leo umber T-shirt/trousers; Max olive vest/shirt/trousers. '
                'Available environments are cafe, street, bedroom, park, bus_stop, studio, classroom. Choose those that serve the story, not all by default. '
                'Keep 6–8 sequences, each a causal action and emotional change, with a coherent recurring prop. Do not write durations or timestamps. '
                'Available actions: '+', '.join(ACTIONS)+'. Available props: '+', '.join(PROPS)+'. '
                'Build the key events from these stageable capabilities. Avoid unsupported spectacle or large crowds. Be specific about what characters do, see and misinterpret. '
                'Return concise complete JSON. Publishing description and keywords must describe this actual story.')
        if short:prompt+=' This is a standalone 45–60 second film: make the story very compact, with its own understandable ending.'
        def check_outline(value):
            if not 6<=len(value['scenes'])<=10 or len({s['id'] for s in value['scenes']})!=len(value['scenes']):raise ValueError('Use 6–10 unique sequence IDs')
            return value
        outline=_cached(writer,draft,'outline',prompt,request,outline_schema(),2600,signature,check_outline)
        directed=[]
        for i,sequence in enumerate(outline['scenes']):
            prompt=('Direct this sequence into 3–5 distinct shots in a layered 2D character film. Use only the supported symbolic choices. '
                    'Preserve the complete story, continuity, chosen cast, clothing and recurring props. Do not invent plot events unsupported by the outline. '
                    'Vary wide/medium/closeup/insert frames, motivated push/pull/pan/hold and positions; no repeated generic tableau. '
                    'Each shot contains actual visible acting and an emotional change, not only camera motion. '
                    'No narrator, internal monologue or explanatory self-talk. Optional short in-world speech only if essential and only selected voices; most shots have no speech. '
                    'Select sound cues for their story purpose; empty cues are valid. Do not add all sample sounds, and use silence when meaningful. '
                    'Non-speech cues have empty speaker/text; speech cues must have actual words, not character labels. '
                    'Caption only meaningful sounds, not music or every little movement. Screen text preferably empty; only necessary small text, never names over actors. '
                    'Actor from/to are screen positions left/center/right; give actors distinct positions. Walking/running travels from to; other actions stay in place. '
                    'An offer and receive must occur together in the same shot with the same prop so their hands can meet. '
                    'Sipping requires cup, drawing requires paper/sketchbook, phone action requires phone. '
                    'focus must be a visible actor. Keep descriptions concise and every camera move motivated. '
                    'Choose score quiet/warm/tense/silent deliberately. No numeric durations or timestamps. Return complete JSON.')
            user={'request':request,'complete_story':outline,'current_sequence':sequence,'previous_sequence':outline['scenes'][i-1] if i else None}
            value=_cached(writer,draft,f'sequence-{i+1:02}',prompt,user,shot_schema(request),3000,signature,lambda v:validate_shots(v,request))
            directed.append(value)
        film=compile_film(outline,directed,request)
        string=STR;thumb=obj({k:string for k in ('hook_text','emotional_promise','composition','image_prompt','source_scene_id')})
        thumb_schema=obj({'thumbnails':{'type':'array','minItems':3,'maxItems':3,'items':thumb}})
        def check_thumbs(v):
            if len(v['thumbnails'])!=3 or any(t['source_scene_id'] not in {s['id'] for s in film['scenes']} for t in v['thumbnails']):raise ValueError('Exactly three thumbnail concepts must reference actual sequence IDs')
            return v
        thumb_prompt=('Design exactly three distinct emotionally compelling original YouTube thumbnail concepts for this actual story. '
            'Use the approved characters/clothes, large expressive face, dark navy/charcoal, amber rim light and cream headline, with a clean upper text zone. '
            'Each uses a different actual scene/composition/emotional hook, not recolors. Headline ideally 1–5 words; honest relatable fear/need/struggle without shaming. '
            'Do not promise a plot or ending absent from the film. source_scene_id must be an existing sequence ID. Image prompts describe a complete original illustration, no logos.')
        film['thumbnails']=_cached(writer,draft,'thumbnails',thumb_prompt,outline,thumb_schema,1800,signature,check_thumbs)['thumbnails']
        film['story_arc']={s['beat']:s['change'] for s in outline['scenes']}
    source={'type':'local_model_directed_film','signature':signature,'writer':MODEL_ID,'revision':MODEL_REVISION,'timing':'app-owned; model uses symbolic pacing'}
    write_package(film,request,out,source)
    return film
