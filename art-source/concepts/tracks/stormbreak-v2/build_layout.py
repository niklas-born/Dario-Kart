"""Create a native vector footprint and sampled Blender-friendly centerline; no raster editing."""
from pathlib import Path
import json, math
out=Path(__file__).parent
start=(500,860)
segments=[
[(500,860),(700,860),(1010,860),(1190,860)],
[(1190,860),(1310,860),(1370,800),(1370,680)],
[(1370,680),(1370,600),(1370,580),(1370,530)],
[(1370,530),(1370,440),(1230,420),(1220,340)],
[(1220,340),(1210,230),(1210,140),(1040,140)],
[(1040,140),(960,140),(900,140),(860,210)],
[(860,210),(800,320),(690,320),(630,220)],
[(630,220),(570,120),(510,140),(430,140)],
[(430,140),(240,140),(150,210),(150,380)],
[(150,380),(150,500),(220,500),(360,520)],
[(360,520),(490,540),(520,640),(440,670)],
[(440,670),(370,700),(250,670),(220,730)],
[(220,730),(140,870),(340,860),(500,860)],
]
points=[]
for seg in segments:
 for i in range(80):
  t=i/80; u=1-t
  points.append([u**3*seg[0][j]+3*u*u*t*seg[1][j]+3*u*t*t*seg[2][j]+t**3*seg[3][j] for j in range(2)])
points.append(list(start))
length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
scale=2160/length
# Verify nonadjacent segments never cross in this 2D concept centerline.
def orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
for i in range(len(points)-1):
 for j in range(i+2,len(points)-1):
  if i==0 and j==len(points)-2: continue
  a,b,c,d=points[i],points[i+1],points[j],points[j+1]
  assert not (orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0), (i,j)
path='M 500 860 '+' '.join('C '+' '.join(f'{x},{y}' for x,y in s[1:]) for s in segments)+' Z'
width=18/scale
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
<rect width="1600" height="1100" fill="#164654"/>
<path d="M65 50 H1500 V965 H70 Z" fill="#a0a587"/>
<path d="M70 940 H1500 V965 H70Z" fill="#d5cbb3"/>
<g fill="#697965"><path d="M270 60H1110V100L820 380L300 410Z"/><path d="M560 370H1170V730H650Z"/></g>
<g stroke="#53605e" stroke-width="3"><rect x="550" y="720" width="220" height="77" rx="6" fill="#e4d5b6"/><rect x="800" y="720" width="110" height="77" rx="6" fill="#d17b36"/>
<rect x="1250" y="150" width="190" height="150" rx="9" fill="#227b83"/><rect x="270" y="310" width="120" height="70" fill="#ba672f"/></g>
<g fill="#e09c40" stroke="#665443" stroke-width="4"><path d="M1030 932v-25h85v25Z"/><path d="M1130 932v-25h85v25Z"/></g>
<path d="{path}" fill="none" stroke="#d6cbb2" stroke-width="{width+18}" stroke-linejoin="round"/>
<path d="{path}" fill="none" stroke="#a04a36" stroke-width="{width+8}" stroke-linejoin="round"/>
<path d="{path}" fill="none" stroke="#f5e4bd" stroke-width="{width+8}" stroke-dasharray="12 12"/>
<path d="{path}" fill="none" stroke="#404b50" stroke-width="{width}" stroke-linejoin="round"/>
<path d="{path}" fill="none" stroke="#f1cc54" stroke-width="2" stroke-dasharray="14 20"/>
<path d="M500 838V882" stroke="white" stroke-width="9"/>
<g fill="#fff3ce" font-family="Arial,sans-serif" font-size="24" font-weight="bold">
<text x="680" y="869">→</text><text x="1370" y="637">↑</text><text x="1030" y="149">←</text><text x="145" y="407">↓</text>
</g>
<g fill="#152c36" font-family="Arial,sans-serif" text-anchor="middle">
<text x="660" y="751" font-size="18">CREAM PIT WORKSHOP</text><text x="850" y="750" font-size="17">ORANGE</text><text x="850" y="773" font-size="17">CONTROL TOWER</text>
<text x="1345" y="209" font-size="23" fill="white">TEAL TURBINE</text><text x="1345" y="237" font-size="23" fill="white">BUILDING</text>
<text x="1080" y="710" font-size="28">01 QUAY START</text><text x="1460" y="470" font-size="21">02</text>
<text x="950" y="90" font-size="23">03 UPPER WORKS</text><text x="335" y="90" font-size="23">04 SWITCHBACK RETURN</text>
<text x="500" y="917" font-size="20">START / FINISH →</text><text x="1120" y="909" font-size="18">TWO DOCK CRANES</text>
</g>
<g font-family="Arial,sans-serif" fill="white"><text x="70" y="1020" font-size="35" font-weight="bold">STORMBREAK V2 · MASTER FOOTPRINT</text><text x="70" y="1060" font-size="21">One closed loop · 18 m road · 2.16 km target · Sea stays outside the circuit · No jumps or bridges</text></g>
</svg>'''
(out/'00-master-layout.svg').write_text(svg)
(out/'layout.json').write_text(json.dumps({'status':'Concept footprint, not a playtested track','direction':'start heads east; then north along the right side, west across top, south on left, return east','length_m':2160,'road_width_m':18,'target_lap_seconds':120,'required_average_speed_m_s':18,'meters_per_svg_unit':scale,'elevation':'Not defined; recommended 0–16 m gentle terrain. Keep start and finish level.','closed':True,'self_intersections':0,'bezier_segments_svg':segments,'centerline_xz_m':[[round((p[0]-500)*scale,3),round((860-p[1])*scale,3)] for p in points]},indent=2))
print(f'Created closed, non-self-crossing layout: 2160 m centerline, 18 m road, scale {scale:.4f} m/svg unit.')
