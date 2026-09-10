# Stormbreak Circuit V2 — concept and modeling handoff

Four environment images generated with the built-in image_gen tool. Retains the teal/orange coastal industrial aesthetic, with a continuous land-supported road and background sea. This is a concept package, not an assembled or playtested Blender circuit.

## Final pictures

1. `01-top-view.png` — overhead environment and route reference.
2. `02-general-view.png` — oblique overview of the whole circuit.
3. `03-start-straight.png` — starting gantry, workshop, control tower and quay.
4. `04-first-bend.png` — broad first left turn and eastern uphill exit.

## Geometry authority

Use `00-master-layout.svg` and `layout.json` for the road footprint. The generated art supplies visual direction; its perspective, dimensions, small architectural details and elevation can vary between images. The overhead art is not a calibrated orthographic render. Landmark rectangles in the vector diagram indicate placement, not building dimensions.

The sampled centerline is closed and checked for nonadjacent segment crossings. This does not verify road-edge clearance, collision, slopes or driving feel. Target road width: 18 m. Centerline length: approximately 2,160 m. At an average 18 m/s (64.8 km/h), a lap takes 120 seconds. Actual lap time must be tuned with the game controller and drifting behavior. Elevation is not encoded; start with a flat blockout, then add gentle rises within a suggested 0–16 m range.

Direction: head east from the south start line, turn left to travel north on the east edge, pass west of the turbine building, turn west through the upper S bends, descend the western bends and reconnect with the same start straight. No jumps, bridges, road gaps or water crossings. Animated surf in the pictures is illustrative: a simple distant water surface is sufficient for the first build.

`layout.json` contains the editable cubic Bezier controls in SVG coordinates, the SVG-to-meter scale and sampled `centerline_xz_m` points. Start is the origin, +X east and +Z north. In Blender use these as XY ground-plane coordinates, with Blender Z for height. The final sampled point repeats the start; omit that duplicate if creating a cyclic spline. `build_layout.py` regenerates the core SVG and JSON.

## Recommended asset workflow

First create and drive a simple continuous road blockout using the master footprint. Then generate or model individual scenery assets and assemble them beside the road. Avoid generating the whole environment as one image-to-3D mesh: that makes road alignment, collisions, scale and editing difficult.

Start with these reusable pieces:

- Teal steel start gantry, with editable span to fit the 18 m road and at least 5 m underside clearance.
- Cream workshop with three teal garage doors; orange control tower as a separate asset.
- Cream barrier segment with separate teal rail, a curb segment and a teal lamp post.
- Orange dock crane, shipping container and small crate; reuse these along the quay.
- A small basalt-rock kit, grass clumps and a simple quay seawall segment.
- Teal turbine building and its orange pipes after the opening stretch is established.

Use meters (1 Blender unit = 1 m), consistent ground-level origins, applied object scale, descriptive names, separate materials and simple collision proxies. Keep roads and curb geometry editable and fitted to the shared spline. Treat the two close views as context references; isolated front/side/back references will improve any asset generated from images.

The opening straight and first corner currently prioritize readable driving and practical asset assembly. Shortcuts and moving hazards can be designed into the blockout later; the V2 images do not specify their placement or claim completed gameplay design.

## Provenance

The original Stormbreak board supplied the aesthetic. The native route guide supplied the corrected topology. The V2 overhead then anchored the other views. Exact generation prompts are in `prompts.json`; the final general-view camera revision is in `general-view-revision-prompt.txt`. `02-general-view-draft.png` is superseded by `02-general-view.png`.
