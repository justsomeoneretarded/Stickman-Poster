"""On-screen text is deliberate: no automatic names, title bars, or captions."""
import re

TEXT_CHOICES={'Essential labels only':'minimal','Captions':'captions','No overlays':'none'}


def safe_label(text,members):
    if not isinstance(text,str):return ''
    text=text.strip()[:64]
    for member in members:
        for value in (member.get('name',''),member.get('id','')):
            if value and re.search(r'\b'+re.escape(value)+r'\b',text,re.I):return ''
    return text


def label_for(scene):
    if scene.get('screen_text','minimal')=='none':return ''
    return safe_label(scene.get('on_screen_text',scene.get('label','')),scene.get('cast_members',[]))
