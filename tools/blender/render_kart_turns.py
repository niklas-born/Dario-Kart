"""Render the six-second steering rehearsals; PNG sequences go in ignored builds/."""
import argparse
from pathlib import Path
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from animate_kart_turns import CONFIGS, ROOT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--kart', choices=list(CONFIGS), required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
cfg = CONFIGS[args.kart]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'art-source/blender/karts' / args.kart / (cfg['stem'] + '-turns.blend')))
scene = bpy.context.scene
scene.render.resolution_percentage = 60
scene.cycles.samples = 8
scene.render.image_settings.file_format = 'PNG'
out = ROOT / 'builds/turn-animation' / args.kart
out.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(out / 'frame-')
bpy.ops.render.render(animation=True)
