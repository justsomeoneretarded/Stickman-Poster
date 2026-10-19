"""Deterministic actor blocking and hand contact for original 2D story scenes."""
import math

STAGINGS = {'talk', 'travel', 'enter', 'chase', 'drink', 'carry', 'handoff', 'react'}


def smooth(value):
    value = min(1, max(0, value))
    return value*value*(3-2*value)


def drink_hand(progress):
    """Rest on tabletop -> lift to mouth -> sip -> replace on tabletop."""
    if progress < .22:
        amount = smooth(progress/.22)
    elif progress < .70:
        amount = 1
    else:
        amount = 1-smooth((progress-.70)/.30)
    return (315-65*amount, 385-141*amount), amount


def blocking_for(cast, speaker, staging):
    ids = [m['id'] for m in cast]
    positions = {1:[.46], 2:[.30,.72], 3:[.20,.50,.80]}[len(ids)]
    result = {cid: {'start': x, 'end': x, 'motion': 'idle', 'prop': 'none', 'floor': 850}
              for cid,x in zip(ids,positions)}
    for i,cid in enumerate(ids):
        result[cid]['phase_offset']=i*.85
    runner = next((m['id'] for m in cast if m['voice']=='male1'), ids[0])
    officer = next((m['id'] for m in cast if m['voice']=='male2' and m['id']!=runner), next((cid for cid in ids if cid!=runner),runner))
    if staging == 'chase':
        result[runner].update(start=.20,end=1.04,motion='run',prop='bag')
        if officer != runner:
            result[officer].update(start=-.05,end=.79,motion='run')
        for cid in ids:
            if cid not in (runner,officer):
                result[cid].update(start=.07,end=.07,floor=800)
    elif staging == 'travel':
        for i,cid in enumerate(ids):
            result[cid].update(start=-.12+i*.19,end=.47+i*.19,motion='walk')
    elif staging == 'enter':
        result[speaker].update(start=-.10,end=.42,motion='walk')
        for i,cid in enumerate(x for x in ids if x!=speaker):
            result[cid].update(start=.64+i*.21,end=.64+i*.21)
    elif staging == 'drink':
        others = [cid for cid in ids if cid!=speaker]
        for i,cid in enumerate(others):
            result[cid].update(start=.17+i*.22,end=.17+i*.22)
        result[speaker].update(start=.62,end=.62,motion='drink',prop='cup')
    elif staging == 'carry':
        result[runner].update(start=.10,end=.76,motion='walk',prop='bag')
        for i,cid in enumerate(x for x in ids if x!=runner):
            result[cid].update(start=.18+i*.18,end=.18+i*.18,floor=790)
    elif staging == 'handoff' and len(ids)>1:
        receiver = next(cid for cid in ids if cid!=runner)
        result[runner].update(start=.22,end=.43,motion='walk',prop='bag')
        result[receiver].update(start=.83,end=.57,motion='walk')
        result[runner]['handoff_to'] = receiver
        for cid in ids:
            if cid not in (runner,receiver):
                result[cid].update(start=.12,end=.12,floor=790)
    elif staging == 'react':
        for i,cid in enumerate(ids):
            result[cid].update(start=positions[i]-.06,end=positions[i],motion='walk')
    return result


def actor_state(track, elapsed, duration, staging='talk'):
    progress = min(1,max(0,elapsed/max(.01,duration)))
    # Chase and travel last through the shot; entrances stop to allow an action.
    travel = progress if staging in {'chase','travel','carry'} else smooth(min(1,progress/.65))
    if staging == 'handoff':
        travel = smooth(min(1,progress/.5))
    x = 1920*(track['start']+(track['end']-track['start'])*travel)
    moving = track['start'] != track['end'] and (travel < .999 or staging in {'chase','travel','carry'})
    phase = abs(x-1920*track['start'])/(160*.83)*math.tau+track.get('phase_offset',0)
    return {'x':x,'floor':track.get('floor',850),'phase':phase,'moving':moving,
            'facing_left':track['end']<track['start'],'progress':progress}


def draw_cast(image,scene,elapsed):
    from PIL import ImageDraw
    from .render import put_character, fit_text, TEAL
    members=scene['cast_members']
    staging=scene.get('staging','talk')
    blocking=scene['blocking']
    colors={'female':'#ea996b','male1':'#79baa9','male2':'#a795df'}
    states={cid:actor_state(track,elapsed,scene['duration'],staging) for cid,track in blocking.items()}
    focus=960
    for member in sorted(members,key=lambda m:states[m['id']]['floor']):
        cid=member['id'];track=blocking[cid];state=states[cid]
        speaking=cid==scene['speaker']
        motion=track['motion']
        action=motion if state['moving'] else (scene['action'] if speaking else 'idle')
        if action in ('walk','run') and not state['moving']:
            action='point' if speaking else 'idle'
        held=track.get('prop','none')
        hand=None
        if motion=='drink':
            hand,_=drink_hand(state['progress']);action='drink'
        elif held=='bag':
            hand=(300,365+math.sin(state['phase'])*8)
        if staging=='handoff':
            giver=next((key for key,t in blocking.items() if t.get('handoff_to')),None)
            if giver:
                receiver=blocking[giver]['handoff_to']
                if cid in (giver,receiver) and state['progress']>.5:
                    # Both characters reach the same shared handle in world space.
                    facing=cid==receiver
                    hand_world=960
                    hand_local=205+(state['x']-hand_world if facing else hand_world-state['x'])/.83
                    hand=(hand_local,350)
                    state['facing_left']=facing
                    held='bag' if cid==(giver if state['progress']<.73 else receiver) else 'none'
                    action='point'
        role=member.get('role','')
        color='#4a87b8' if role=='police' else colors.get(member['voice'],'#ea996b')
        put_character(image,state['x'],state['floor'],.83,elapsed,action,
                      color=color,speaking=speaking,gait_phase=state['phase'],
                      facing_left=state['facing_left'] if state['moving'] or staging=='handoff' else state['x']>1250,
                      hand_target=hand,held_prop=held,role=role,
                      tilt=0 if state['moving'] else math.sin(elapsed*1.6)*1.0)
        if speaking:
            focus=state['x']
    if scene.get('prop')=='cup' and not any(t.get('prop')=='cup' for t in blocking.values()) and scene['location'] in ('room','cafe'):
        from .render import held_object
        draw=ImageDraw.Draw(image)
        table=710 if scene['location']=='cafe' else 650
        held_object(draw,(1290,table-21),'cup')
    return focus
