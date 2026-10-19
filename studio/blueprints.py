"""Renderable comic premises, not canned dialogue. The model writes every spoken line."""
import math


def comic_blueprint(title,voices,minutes):
    text=title.lower()
    if 'bench' in text:
        car='car' in text
        load='car' if car else 'barbell'
        theme='a full-sized car' if car else 'a four-hundred-pound barbell'
        gags=[
            ('lift','gym','wide',f'Open by visibly bench-pressing {theme}. The friend expected a normal workout, not this absurd sight.',10),
            ('react','gym','close','The spotter is shocked: a normal gym job has suddenly become a very strange job. Warm teasing, not fear.',7),
            ('lift','gym','wide','The lifter treats the huge load as a casual warm-up while the friend tries to sound unimpressed.',9),
            ('talk','gym','close','The friend tries to count reps but is distracted by the ridiculous size of the load. Contrast huge power with simple counting.',7),
            ('reveal','street','wide','The same car is now parked normally. Being incredibly strong still does not create an empty parking space.' if car else 'After the impressive workout, the hero still has to remember where they left their water bottle. Power has not improved memory.',9),
            ('react','street','close','The friend finds the hero’s tiny ordinary inconvenience much funnier than the impressive feat. Keep it warm, not judgmental.',6),
            ('lift','gym','wide','Back to the impressive lift. The friend acts like an announcer for an absurdly ordinary gym session. Escalate the joke without adding powers.',9),
            ('talk','gym','close','The hero admits the hardest part of gym day is still choosing a playlist. Banter about an ordinary decision next to extraordinary strength.',7),
            ('react','gym','close','The friend wants to know whether the car needs its own gym membership.' if car else 'The friend jokingly asks whether the weights owe the hero rent for spending so much time overhead.',10),
            ('lift','gym','wide','The hero completes another relaxed rep and the friend becomes hilariously formal about counting it. No danger, crashes or fake reveal.',8),
            ('talk','gym','close','The hero is proud of the lift but the friend has discovered an even sillier gym technicality. Build toward the membership callback.' if car else 'The friend is impressed but still insists the hero put the weights back like everyone else. An ordinary request after a huge feat.',7),
            ('lift','gym','wide','Final callback: the car now needs its own gym membership, so the hero has become their own vehicle’s personal trainer. Land the specific joke, no lesson.' if car else 'Final callback: the hero crushed four hundred pounds, but the friend still wins the argument over who chooses the workout playlist. Warm comic ending.',10),
        ]
    elif 'fly' in text or 'flying' in text:
        load='none'
        gags=[
            ('fly','rooftop','wide','Open already flying above the city, delighted to skip road traffic. The very next inconvenience is pigeon rush hour.',10),
            ('react','rooftop','close','The grounded friend finds it hilarious that flying has simply introduced a new category of commute complaints.',8),
            ('fly','rooftop','wide','The hero cruises through the air while complaining that the phone’s navigation still thinks they are on a road. Ordinary GPS, extraordinary commute.',9),
            ('talk','rooftop','close','The friend suggests an absurdly polite solution to sharing the sky with birds. Keep the banter warm and specific.',7),
            ('fly','rooftop','wide','The hero learns that choosing a good flying hairstyle is now part of getting ready. No extra powers, just a silly practical detail.',8),
            ('react','park','close','The friend admires the flying but is more interested in whether it gets them to coffee before the queue forms.',7),
            ('drink','cafe','medium','A coffee break after the flight. Flying is amazing, but the hero still likes the ordinary pleasure of sitting down with a warm drink.',8),
            ('talk','cafe','close','The friend asks whether flying means the hero is now responsible for the coffee run. A gentle everyday joke, not an ethical lesson.',9),
            ('fly','rooftop','wide','The hero takes off happily again, now treating the daily flight as an overly glamorous trip for coffee.',9),
            ('react','rooftop','close','The friend gives a mock traffic update for pigeon rush hour, calling back to the opening.',8),
            ('fly','rooftop','wide','The hero enjoys the sky and makes a very specific, silly complaint about the airborne commute.',8),
            ('fly','rooftop','wide','Final callback: the hero can fly anywhere, but the friend has still turned them into the coffee delivery service. End on warm teasing and pigeon traffic.',10),
        ]
    else:return None
    count=min(90,max(6,math.ceil(minutes*10)))
    plan=[]
    for i in range(count):
        gag_index=round(i*(len(gags)-1)/max(1,count-1))
        stage,location,shot,purpose,score=gags[gag_index]
        previous=plan[-1].get('gag_id') if plan else None
        repeated=previous==gag_index
        if repeated:
            stage='talk' if i%2 else 'react';shot='close'
            purpose+=' Continue the previous exchange with a NEW response or comic button; do not repeat its setup.'
        plan.append({'speaker':voices[i%len(voices)],'location':location,'staging':stage,'shot':shot,
                     'prop':load if stage=='lift' else 'car' if 'car' in text and stage=='reveal' else 'cup' if stage=='drink' else 'none',
                     'purpose':purpose,'short_score':score,'gag_id':gag_index,
                     'comic_role':'hook' if i==0 else 'payoff' if i==count-1 else 'escalation'})
    return plan
