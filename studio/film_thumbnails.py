"""Optional reference-guided thumbnail images; requires explicitly configured API access.

Never invoked by the free planning workflow unless its image option is selected.
The approved source art is read only; results are new files in the package.
"""
import argparse
import base64
import io
import json
import os
import secrets
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image,ImageOps

API='https://api.openai.com/v1/images/edits'
MODEL='gpt-image-1'


def multipart(fields,reference):
    boundary='studio-'+secrets.token_hex(16);parts=[]
    for name,value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    references=reference if isinstance(reference,list) else [reference]
    for index,path in enumerate(references):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="approved-reference-{index}.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
        parts.append(Path(path).read_bytes());parts.append(b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts),'multipart/form-data; boundary='+boundary


def generate_thumbnails(package,reference):
    key=os.environ.get('OPENAI_API_KEY')
    if not key:raise ValueError('Three thumbnail images require the OPENAI_API_KEY repository secret. Planning alone needs no image API.')
    package=Path(package);briefs=json.loads((package/'thumbnail-briefs.json').read_text())
    if len(briefs)!=3:raise ValueError('Expected exactly three thumbnail briefs')
    output=package/'thumbnails';output.mkdir(exist_ok=True)
    status_path=package/'delivery-status.json';status=json.loads(status_path.read_text())
    request=json.loads((package/'request.json').read_text())
    from .film_concept import CAST
    allowed=', '.join(CAST[v] for v in request.get('characters',list(CAST)))
    status['thumbnail_images_rendered']=0;status['thumbnail_backend']=MODEL
    status_path.write_text(json.dumps(status,indent=2)+'\n')
    for i,brief in enumerate(briefs,1):
        prompt=('Create a new original cinematic illustrated YouTube thumbnail using the attached approved image ONLY as a character, clothing, palette and finish reference. '
                'Preserve identity and clothes, but create the new composition described below. Do not reproduce the old headline or original composition. '
                'Keep all critical content within the centered 16:9 safe area of the 1536x1024 canvas, with expendable margins above and below for cropping. '
                'Emotion readable at phone size. Strong contrast, textured cream-white headline, charcoal/navy shadows and warm rim lighting. '
                'Do not add watermarks, labels, extra fingers, or unsupported plot promises. '
                +'Only these selected characters may appear: '+allowed+'. '
                +brief['image_prompt']+'\nThe only headline is: '+brief['hook_text'])
        references=[reference]
        cast_reference=Path('designs/day-one-pivot/three-character-concepts.png')
        if cast_reference.is_file() and cast_reference!=Path(reference):references.append(cast_reference)
        payload,content_type=multipart({'model':MODEL,'prompt':prompt,'size':'1536x1024','quality':'high','n':'1'},references)
        req=urllib.request.Request(API,data=payload,headers={'Authorization':'Bearer '+key,'Content-Type':content_type})
        try:
            with urllib.request.urlopen(req,timeout=600) as response:result=json.load(response)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Thumbnail image API returned HTTP {e.code}; completed images are retained. Check API access/billing; no placeholder image was substituted.') from None
        item=result['data'][0]
        if not item.get('b64_json'):raise RuntimeError('Image API did not return image bytes')
        data=base64.b64decode(item['b64_json'],validate=True)
        with Image.open(io.BytesIO(data)) as im:
            im.load();ImageOps.fit(im.convert('RGB'),(1280,720),method=Image.Resampling.LANCZOS).save(output/f'thumbnail-{i}.png')
        status['thumbnail_images_rendered']=i;status_path.write_text(json.dumps(status,indent=2)+'\n')
    status['missing']=[m for m in status['missing'] if 'thumbnail' not in m.lower()]
    status_path.write_text(json.dumps(status,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True)
    p.add_argument('--reference',default='designs/day-one-pivot/thumbnail-direction.png')
    a=p.parse_args();generate_thumbnails(a.package,a.reference)


if __name__=='__main__':main()
