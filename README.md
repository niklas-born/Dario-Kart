# Dario Kart

A fast, expressive 3D kart racer: drifting, item battles, huge jumps, changing scenery, moving hazards, boost pads, and surfaces that change handling. Original characters, worlds, and items; Mario Kart is the gameplay reference.

**Stack: Unity 6.3 LTS + C# + Universal Render Pipeline (URP), with Blender for asset creation.** The game runs locally on macOS and Windows. The long-term destination is the user's DIY Wii-style console, with phones as controllers. See [the engine decision](docs/engine-decision.md) and [phone controller integration](docs/phone-controllers.md).

## Current state

Repository foundation, not a playable game. Includes a minimal Unity project seed, typed content definitions, an editor setup command, a static Blender-to-FBX export pipeline, and development milestones. Driving, AI, items, and finished courses are planned, not implemented.

Blender 5.2.1 LTS is available on the setup machine. Unity and Git LFS were not found. Unity compilation, package resolution, scene rendering, and builds still require the editor. No engine installation or paid assets are included.

## Layout

```text
game/                         Open this folder in Unity Hub
  Assets/_DarioKart/
    Scripts/Runtime/          C# content definitions and gameplay modules
    Scripts/Editor/           Setup and asset import tools
    Art/                      Exported models, textures, materials, animation, VFX
    Audio/                    Runtime clips and mixer assets
    Data/                     Kart, surface, item, and track ScriptableObjects
    Prefabs/                  Reusable gameplay objects that reference imported art
    Scenes/                   Bootstrap, menus, development scenes, courses
    Settings/                 URP, input, physics, and quality configuration
    UI/                       HUD and menus
  Packages/                   Pinned direct dependencies; resolved lock follows first open
  ProjectSettings/           Pinned editor; remaining settings generated on first open
art-source/                   Editable .blend files, textures, audio sources, references
tools/blender/                Repeatable static mesh export and pipeline fixture
integrations/phone-controllers/ Protocol contract and future DIY console adapter
docs/                         Architecture, art pipeline, vision, setup, roadmap
builds/                       Local game builds (ignored)
```

## Start here

Current character art: [eight monster racers with distinct kart designs](art-source/concepts/racers/round-02/README.md) plus [the final four completed from the supplied composite sheet](art-source/concepts/racers/round-03/README.md). Each concept sheet includes a three-quarter, front, side and rear view. The roster now has twelve racers, always in vehicles.

First 3D driver: [Riff's Blender model, concept comparisons, and poseable exports](art-source/blender/characters/riff/README.md). Driver production is proceeding one character at a time.

Riff now has his [Streamliner kart](art-source/blender/karts/streamliner/README.md), with a fitted cockpit, exposed suspension, turning and spinning wheels, and a combined Blender scene.

1. Follow [setup](docs/setup.md) to install the pinned Unity editor, open `game/`, and run **Dario Kart → Setup Foundation**.
2. Read [architecture](docs/architecture.md) for how code, scenes, prefabs, and data connect.
3. Read [asset pipeline](docs/asset-pipeline.md) before adding Blender work.
4. Build the [first vertical slice](docs/roadmap.md): one great kart and one great course.

Repository checks (Python 3, no third-party dependencies):

```sh
python3 tools/check_repo.py
```

Source assets and exports belong in version control, using Git LFS for binary art. Unity `.meta` files and text scenes/prefabs belong in ordinary Git. See [setup](docs/setup.md) before the first commit.
