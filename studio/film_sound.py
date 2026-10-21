"""Dry Turbo dialogue, original restrained motif and explicitly directed procedural foley."""
import json
import math
import subprocess
import wave
from pathlib import Path
import numpy as np
from .film_concept import CAST,write_package

SR=24000


def wav_read(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar',str(SR),'pipe:1'])
    return np.frombuffer(raw,dtype='<f4').copy()


def write_wav(path,a):
    with wave.open(str(path),'wb') as f:
        channels=1 if a.ndim==1 else a.shape[1]
        f.setparams((channels,2,SR,0,'NONE','not compressed'))
        f.writeframes((np.clip(a,-.99,.99)*32767).astype('<i2').tobytes())


def voice_assets(package,model_dir,profiles='voices/cast-profiles.json'):
    from .voice import synthesize_scenes
    package=Path(package);film=json.loads((package/'film.json').read_text())
    mapping=json.loads(Path(profiles).read_text());base=Path(profiles).parent;result={}
    for key,name in CAST.items():
        scenes=[]
        for sequence in film['scenes']:
            for shot in sequence['shots']:
                for index,c in enumerate(shot['cues']):
                    if c['asset']=='speech' and c['speaker']==name:scenes.append({'id':f'{shot["id"]}-{index}','narration':c['text']})
        if not scenes:continue
        directory=package/'audio'/'voices'/key
        manifest=synthesize_scenes({'scenes':scenes},base/mapping[key],directory,model_dir=model_dir)
        for row in manifest['entries']:result[row['scene_id']]=str((directory/row['file']).resolve())
    (package/'voice-assets.json').write_text(json.dumps(result,indent=2)+'\n')


def tone(freq,n,decay=1):
    t=np.arange(n)/SR
    return (np.sin(2*np.pi*freq*t)+.23*np.sin(2*np.pi*freq*2.006*t)+.1*np.sin(2*np.pi*freq*3.012*t))*(1-np.exp(-t*70))*np.exp(-t/decay)


def foley(asset,seconds,seed):
    n=max(1,round(seconds*SR));t=np.arange(n)/SR;rng=np.random.default_rng(seed);noise=rng.normal(0,1,n)
    smooth=np.convolve(noise,np.ones(17)/17,mode='same')
    if asset in ('room','rain','wind'):
        a=smooth*({'room':.008,'rain':.022,'wind':.018}[asset])
        if asset=='wind':a*=.6+.4*np.sin(t*1.7)**2
    elif asset=='phone_vibration':a=(np.sin(t*2*np.pi*112)+.2*np.sin(t*2*np.pi*224))*.06*(np.sin(t*2*np.pi*3)>0)
    elif asset=='car_horn':a=(np.sin(t*2*np.pi*370)+np.sin(t*2*np.pi*466))*.06*(t<.65)
    elif asset=='door_bell':a=tone(1174.66,n,.45)*.07+tone(1567.98,n,.3)*.025
    elif asset=='cup_set':a=(tone(1800,n,.045)*.06+smooth*np.exp(-t*55)*.1)
    elif asset=='coin_drop':a=sum(tone(f,n,.15)*.025 for f in (1900,2671,3350));a*=np.exp(-t*7)
    elif asset in ('paper_rustle','pencil','chair_scrape'):
        a=smooth*({'paper_rustle':.05,'pencil':.035,'chair_scrape':.09}[asset])*(np.sin(t*37)**2)*np.exp(-t*2)
    elif asset=='steps':
        a=np.zeros(n)
        for at in np.arange(0,seconds,.5):
            begin=int(at*SR);length=min(int(.13*SR),n-begin);tt=np.arange(length)/SR
            a[begin:begin+length]+=(np.sin(tt*2*np.pi*82)+.4*rng.normal(0,1,length))*.06*np.exp(-tt*35)
    else:raise ValueError('Unsupported sound asset: '+asset)
    fade=np.minimum(t/.025,1)*np.minimum((seconds-t)/.07,1)
    return np.asarray(a*fade,dtype=np.float32)


def music(seconds,mood,index):
    n=round(seconds*SR);a=np.zeros(n,dtype=np.float32)
    if mood=='silent':return a
    roots={'quiet':(220,261.63,329.63),'warm':(220,277.18,329.63),'tense':(196,233.08,293.66)}
    notes=roots[mood]
    for i,at in enumerate(np.arange(.2,seconds,3.2)):
        begin=int(at*SR);length=min(n-begin,int(4.5*SR));freq=notes[(i+index)%3]
        a[begin:begin+length]+=tone(freq,length,1.6)*.025
    fade=np.minimum(np.arange(n)/(SR*.3),1)*np.minimum(np.arange(n)[::-1]/(SR*.6),1)
    return a*fade


def rebuild_sequences(film):
    for sequence in film['scenes']:
        offset=0;sequence['cues']=[];sequence['dialogue']=[];sequence['screen_text']=[]
        for shot in sequence['shots']:
            shot['start_in_sequence']=offset
            for c in shot['cues']:
                asset=c['asset'];kind='speech' if asset=='speech' else 'silence' if asset=='silence' else 'ambience' if asset in ('rain','room','wind') else 'foley'
                sequence['cues'].append({'kind':kind,'start_seconds':offset+c['start_seconds'],'end_seconds':offset+c['end_seconds'],
                    'detail':asset,'reason':c['reason'],'caption':c['caption'] if asset!='silence' else '',
                    'speaker':c['speaker'],'text':c['text'],'offscreen':c['offscreen']})
                if asset=='speech':sequence['dialogue'].append({'character':c['speaker'],'text':c['text']})
            if shot['screen_text']:sequence['screen_text'].append({'start_seconds':offset+min(.2,shot['seconds']*.1),'end_seconds':offset+shot['seconds']-min(.2,shot['seconds']*.1),'text':shot['screen_text'],'purpose':shot['description']})
            offset+=shot['seconds']
        sequence['seconds']=offset


def mix(package):
    package=Path(package);film=json.loads((package/'film.json').read_text());request=json.loads((package/'request.json').read_text());fps=request['fps']
    paths=json.loads((package/'voice-assets.json').read_text()) if (package/'voice-assets.json').exists() else {};voice={}
    shots=[s for seq in film['scenes'] for s in seq['shots']]
    # Extend acting instead of cutting speech or squeezing a line to a target length.
    for shot in shots:
        previous_speech_end=-.15
        for index,c in enumerate(shot['cues']):
            if c['asset']!='speech':continue
            key=f'{shot["id"]}-{index}'
            if key not in paths:raise ValueError('Missing real dialogue audio for '+key+'; no silent speech fallback')
            a=wav_read(paths[key]);voice[key]=a
            start=max(c['start_seconds'],previous_speech_end+.15);c['start_seconds']=start;c['end_seconds']=start+len(a)/SR
            previous_speech_end=c['end_seconds'];shot['seconds']=max(shot['seconds'],previous_speech_end+.4)
        shot['seconds']=math.ceil(shot['seconds']*fps-1e-8)/fps
    total=sum(round(s['seconds']*SR) for s in shots);full=np.zeros((total,2),dtype=np.float32);offset=0
    for i,shot in enumerate(shots):
        n=round(shot['seconds']*SR);bed=music(shot['seconds'],shot['score'],i);effects=np.zeros(n,dtype=np.float32);dialogue=np.zeros((n,2),dtype=np.float32)
        duck=np.ones(n,dtype=np.float32)
        for j,c in enumerate(shot['cues']):
            start=round(c['start_seconds']*SR);end=min(n,round(c['end_seconds']*SR))
            if c['asset']=='speech':
                a=voice[f'{shot["id"]}-{j}'];a=a/(max(.15,float(np.max(abs(a)))))*.3
                if c['offscreen']:a=np.convolve(a,np.ones(5)/5,mode='same')*.65
                actor=next((a for a in shot['actors'] if a['character']==c['speaker']),None)
                pos={'left':.2,'center':.5,'right':.8}[actor['from']] if actor else .75
                length=min(len(a),n-start)
                dialogue[start:start+length,0]+=a[:length]*math.cos(pos*math.pi/2);dialogue[start:start+length,1]+=a[:length]*math.sin(pos*math.pi/2)
                duck[max(0,start-int(SR*.12)):min(n,end+int(SR*.2))]=.22
            elif c['asset']=='silence':bed[start:end]=0;effects[start:end]=0
            else:
                duration=(n-start)/SR if c['asset'] in ('room','rain','wind') else (end-start)/SR
                a=foley(c['asset'],duration,100+i*11+j);length=min(len(a),n-start);effects[start:start+length]+=a[:length]
        mono=bed*duck+effects;mixdown=np.stack((mono,mono),axis=1)+dialogue
        full[offset:offset+n]=mixdown;offset+=n
    peak=float(np.max(abs(full)));gain=min(2.5,.85/max(.0001,peak));full*=gain
    folder=package/'audio';folder.mkdir(exist_ok=True);write_wav(folder/'mix.wav',full)
    report={'seconds':len(full)/SR,'sample_rate':SR,'peak_dbfs':round(20*math.log10(max(1e-9,float(np.max(abs(full))))),2),
        'clipped_samples':int(np.sum(abs(full)>=.999)),'speech_clips':len(voice),'music':'original synthesized sparse motif, shot-directed',
        'foley':'procedural synthesis selected by explicit story-aware director cues','voice':'dry Chatterbox Turbo; no added echo or reverb' if voice else 'no speech directed; no TTS fallback','review':'Technical signal checks; listening review is still needed.'}
    (folder/'mix-report.json').write_text(json.dumps(report,indent=2)+'\n')
    rebuild_sequences(film);source=json.loads((package/'production-spec.json').read_text())['source'];write_package(film,request,package,source)
    (package/'subtitle-notes.txt').write_text('Line-level dialogue timing uses measured generated audio. Sound-caption times follow rendered cues. Not word-aligned. No captions are automatically burned into picture.\n')
    return report
