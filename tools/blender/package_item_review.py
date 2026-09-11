"""Build contact sheets and documentation from actual Blender review renders.

Run with ordinary Python + Pillow, not Blender. No image generation is used.
"""
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art-source/blender/items'
ITEMS=[('comet-core','Comet Core','03'),('snaptrap','Snaptrap','03'),
       ('turbo-battery','Turbo Battery','02'),('guardian-orb','Guardian Orb','03'),
       ('magnet-mine','Magnet Mine','02'),('phase-gear','Phase Gear','02'),
       ('route-painter','Route Painter','02'),('swap-beacon','Swap Beacon','03')]
NOTES={
 'comet-core':'Three passes: irregular basalt cells, narrower molten fissures, deeper orange rock, forged cage, rivets, orbiting rocks, and flame tips.',
 'snaptrap':'Three passes: connected dark-red mouth backing, separated upper/lower jaw parts, enlarged fangs, lowered foliage, tongue, and corrected warning-light seating.',
 'turbo-battery':'Two passes: purple end caps, lime reservoir, thin cyan glass, raised lightning badge, bubbles, and reduced glass refraction to keep the energy cell visible.',
 'guardian-orb':'Three passes: flattened eye assembly, narrower recessed seams, larger staggered ceramic panels, finer iris fibers, side ports, and floating cyan shield arcs.',
 'magnet-mine':'Two passes: broad hazard-striped puck, rounded horseshoe and silver poles, shorter pole height relative to the red beacon, front hatch, and mounting bolts.',
 'phase-gear':'Two passes: ten-tooth open-center gear, softened tooth corners, cyan-to-violet material bands, translucent body, and separate luminous edge geometry.',
 'route-painter':'Two passes: rolled can rims, inset spray aperture, drips separated from the curved tapering road graphic, raised road dashes, and optional cyan paint swoosh.',
 'swap-beacon':'Three passes: faceted crystal, separated red/blue ribbon heights, a reversed blue arrowhead, and a broad upper diamond with a distinct smaller spectral point below the loops.'}

def font(size):return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',size)

overview=Image.new('RGB',(1920,1190),'#211A2B');d=ImageDraw.Draw(overview)
d.text((32,22),'ITEMS / BLENDER MODELS',font=font(42),fill='#FFFFFF')
d.text((34,80),'Eight editable models  /  Actual mesh renders  /  Preserved iteration passes',font=font(22),fill='#C9B7D2')
comparison=Image.new('RGB',(1440,2410),'#211A2B');cd=ImageDraw.Draw(comparison)
cd.text((28,22),'CONCEPT  /  MODELED GEOMETRY',font=font(36),fill='white')
cd.text((30,72),'Supplied artwork at left. Blender render at right. Back surfaces are inferred.',font=font(20),fill='#C9B7D2')
concept=Image.open(ROOT/'art-source/concepts/items/item-concepts.png').convert('RGB')
table=[]
for i,(slug,title,rev) in enumerate(ITEMS):
    folder=OUT/slug;final=folder/'review/final';final.mkdir(exist_ok=True)
    for view in ['hero','front','rear']:
        src=folder/'review'/('v'+rev)/(view+'.png')
        assert src.exists(),src
        if not (final/(view+'.png')).exists():shutil.copyfile(src,final/(view+'.png'))
    manifest=json.loads((folder/'exports'/(slug+'.manifest.json')).read_text())
    validation=json.loads((folder/'exports/validation.json').read_text())
    assert validation['passed']
    x=20+(i%4)*475;y=128+(i//4)*517
    d.rounded_rectangle((x,y,x+459,y+500),radius=16,fill='#392A40')
    d.text((x+15,y+12),f'{i+1:02d}  {title}',font=font(24),fill='white')
    render=Image.open(final/'hero.png').convert('RGB')
    overview.paste(render.resize((430,430),Image.Resampling.LANCZOS),(x+15,y+50))
    d.text((x+16,y+482),f'v{rev}  /  {manifest["triangles"]:,} triangles',font=font(15),fill='#D8C5DE')
    x=20+(i%2)*710;y=118+(i//2)*570
    cd.rounded_rectangle((x,y,x+690,y+548),radius=14,fill='#392A40')
    cd.text((x+20,y+16),f'{i+1:02d}  {title}  /  v{rev}',font=font(27),fill='white')
    crop=concept.crop((i*192+6,123,(i+1)*192-4,338))
    crop.save(ROOT/'art-source/concepts/items'/(slug+'.png'))
    crop=ImageOps.contain(crop,(213,328),Image.Resampling.LANCZOS)
    comparison.paste(crop,(x+22,y+124))
    comparison.paste(render.resize((420,420),Image.Resampling.LANCZOS),(x+252,y+76))
    cd.text((x+22,y+478),'CONCEPT',font=font(17),fill='#C9B7D2')
    cd.text((x+272,y+510),'BLENDER RENDER',font=font(17),fill='#C9B7D2')
    readme=f'''# {title}

[Editable Blender model]({slug}.blend) · [Lit review scene]({slug}-review.blend) · [FBX](exports/{slug}.fbx) · [GLB](exports/{slug}.glb)

![Actual Blender render](review/final/hero.png)

{NOTES[slug]}

[Front](review/final/front.png) · [Rear](review/final/rear.png) · [Concept](../../../concepts/items/{slug}.png) · [Export validation](exports/validation.json)

The stable source preserves named editable parts in `EXPORT` and optional decorative effects in `EFFECTS`. Numbered `.blend` files and their `review/vXX` renders preserve the iteration history. The review scene has lighting, a camera, and the packed original concept sheet; these are excluded from exchange assets.

The exchange package has **{manifest['triangles']:,} triangles** across **{manifest['meshObjects']} material groups**, including optional effects. UVs, applied transforms, normals, mesh counts, dimensions, and studio exclusion are checked by the shared validator. Material colors use constant PBR values, without Blender-only procedural textures. GLB includes emission/transmission material extensions where used. FBX requires explicit URP materials; the material values and export pivot are recorded in [the manifest](exports/{slug}.manifest.json).

This is a static item art asset. Source jaw and other component pieces can be edited independently; the exchange meshes consolidate by material and are not rigged. Runtime animation, colliders, LODs, shader effects, gameplay behavior, and Unity appearance are not implemented or tested here. Unseen rear surfaces are a consistent modeled interpretation of the supplied single-view concept.

Rebuild the current design with Blender 5.2.1 LTS:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/build_items.py -- --item {slug} --revision {rev} --final --views hero,front,rear
```

Choose a new revision number to preserve an existing source pass. The stable model, review scene, and exchange files are refreshed on final packaging.
'''
    (folder/'README.md').write_text(readme)
    table.append(f'| [{title}]({slug}/README.md) | {rev} | {manifest["triangles"]:,} | [{slug}.blend]({slug}/{slug}.blend) |')

overview.save(OUT/'item-models-overview.png')
comparison.save(OUT/'concept-model-comparison.png')
(OUT/'README.md').write_text('''# Item models

Eight original Blender item models built one at a time from the [supplied concept sheet](../../concepts/items/item-concepts.png). Each item has two or three reviewed geometry passes, a clean editable source, a lit review scene, and UV-mapped FBX/GLB exchange assets.

![Eight actual Blender renders](item-models-overview.png)

[Concept-to-model comparison](concept-model-comparison.png) · [Validation results](validation.json)

| Item | Latest pass | Exchange triangles including effects | Blender source |
| --- | --- | ---: | --- |
'''+ '\n'.join(table)+'''

## Editing and importing

The source scenes use meters, Z up, and −Y forward. `EXPORT` contains the editable item geometry, while `EFFECTS` contains removable sparks, orbit arcs, paint trails, or decorative crystal flecks. Camera, lights, floor, and packed concept art live in the separate review scene. Exchange files use Y up and consolidate geometry by material. Floating items export around their visual center; Snaptrap and Magnet Mine use the base origin. The exact source-to-export pivot offset is in each manifest.

All materials use portable constant PBR values. FBX material values are documented for explicit URP setup; GLB preserves its supported material properties, including emission/transmission extensions. Final previews use Standard color management at −1 EV to retain the saturated concept palette; earlier pass renders preserve their original lighting. The Blender review lighting and compositor glow are presentation settings, and need a runtime lighting/bloom setup to reproduce in Unity.

The models are static art assets for subsequent engine integration. They do not yet include Unity wrapper prefabs, colliders, item behavior, animation rigs, texture atlases, LODs, or a measured target-device performance budget. Source pieces remain editable, including Snaptrap's separate jaw assemblies. Rear surfaces and depth are inferred from the single supplied concept view. Appearance matching is a visual review, not a measured claim of identical reconstruction.

## Verification and rebuild

`tools/blender/build_items.py` generates and packages each item independently. `tools/blender/verify_items.py` freshly imports each FBX and checks geometry, UVs, counts, scale, and exclusion of studio objects; it also inspects GLB normals and UVs. All eight exchange packages passed. Unity appearance and gameplay are not tested.

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python-exit-code 1 --python tools/blender/verify_items.py
```

`tools/blender/package_item_review.py` uses Pillow to assemble the contact sheets from actual renders. Per-item READMEs describe the visual corrections and link directly to source, exchange files, and front/rear views.
''')

register=ROOT/'art-source/asset-register.json'
data=json.loads(register.read_text())
existing={a['id'] for a in data['assets']}
for slug,title,rev in ITEMS:
    if 'item-'+slug not in existing:
        data['assets'].append({'id':'item-'+slug,'source':f'art-source/blender/items/{slug}/{slug}.blend',
          'author':'Dario Kart project','origin':'Original Blender geometry modeled from the user-supplied item concept sheet',
          'reference':'art-source/concepts/items/item-concepts.png','builder':'tools/blender/build_items.py',
          'validation':'tools/blender/verify_items.py','purpose':title+' static item model and exchange art; Unity integration pending',
          'review':f'art-source/blender/items/{slug}/README.md'})
register.write_text(json.dumps(data,indent=2)+'\n')
print('Packaged overview, comparisons, eight READMEs, and asset provenance.')
