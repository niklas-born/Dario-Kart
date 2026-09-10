"""Verify animated GLB channels and that the accepted source assemblies are unchanged."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
for kart, stem, prefix in [('streamliner', 'riff-streamliner', ''), ('dune-hopper', 'grit-dune-hopper', 'Dune_')]:
    folder = ROOT / 'art-source/blender/karts' / kart
    report_path = folder / 'exports/turn-animation.validation.json'
    report = json.loads(report_path.read_text())
    source = ROOT / report['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == report['sourceSha256'], 'Accepted source changed'
    glb = folder / 'exports' / (stem + '-turns.glb')
    data = glb.read_bytes()
    magic, version, total = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and total == len(data)
    length, kind = struct.unpack_from('<I4s', data, 12)
    assert kind == b'JSON'
    doc = json.loads(data[20:20 + length])
    assert len(doc['skins']) == 1 and len(doc['skins'][0]['joints']) == 14
    assert len(doc['animations']) == 1
    animation = doc['animations'][0]
    animated = {doc['nodes'][c['target']['node']]['name']: c for c in animation['channels']
                if c['target']['path'] == 'rotation'}
    expected = {'head', 'chest', 'hand.L', 'hand.R', 'forearm.L', 'forearm.R'}
    expected.update(prefix + 'Spin_' + side for side in ('FL', 'FR', 'RL', 'RR'))
    expected.update(prefix + 'Steer_' + side for side in ('FL', 'FR'))
    assert expected <= animated.keys(), expected - animated.keys()
    assert not any(prefix + 'Steer_' + side in animated for side in ('RL', 'RR'))
    assert 'Dune_Spare_Mount' not in animated
    for name in expected:
        sampler = animation['samplers'][animated[name]['sampler']]
        times = doc['accessors'][sampler['input']]
        assert times['count'] > 2 and abs(times['max'][0] - times['min'][0] - 6) < .01, (name, times)
    assert any(c['target']['path'] == 'weights' for c in animation['channels']), 'Blink was lost'
    assert not doc.get('cameras')
    report.update(glbAnimationVerified=True, glbSha256=hashlib.sha256(data).hexdigest(),
                  glbBakedDurationSeconds=6, driverBones=14, acceptedSourceUnchanged=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(stem + ': baked steering, rolling, driver pose and blink verified; source unchanged')
