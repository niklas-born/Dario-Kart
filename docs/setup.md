# Local setup

## Tools

- Unity Hub and **Unity 6000.3.23f1** (Unity 6.3 LTS), Apple Silicon editor on this Mac. [Official release and downloads](https://unity.com/releases/editor/whats-new/6000.3.23f1).
- Blender **5.2.1 LTS** is installed on the setup machine. Use a consistent Blender version across asset contributors.
- Git and Git LFS. Git is initialized; LFS was not found during setup. Install Git LFS using your preferred package manager, then run `git lfs install --local` inside this repo before staging binary assets.
- A C# editor such as VS Code or Rider. Unity supplies its scripting compiler; a standalone .NET SDK is not required to open this seed.
- Python 3 for repository checks; Blender runs export scripts using its bundled Python.

## First Unity open

1. In Hub choose **Add project from disk** and select `game/` in this repository. Do not create a template over the existing folder. Use the exact pinned editor version.
2. Let Unity resolve `Packages/manifest.json`, generate missing default project settings, and import assets. Network access and an activated Unity license are needed. This seed deliberately contains no fabricated package lock or editor-generated scene YAML.
3. Wait for compilation. Run **Dario Kart → Setup Foundation**. It creates the URP asset/renderer, sets linear color and 60 Hz physics, enables text serialization and visible metadata, creates kart/surface defaults, and generates the ramp preview scene and prefab when the FBX is present. It creates missing content and preserves existing content. It applies the baseline project settings each time, so use it as initial setup rather than a daily tuning command.
4. Open `Assets/_DarioKart/Scenes/Development/AssetPreview.unity`. Check the ramp geometry, 4 × 8 × 2 m bounds, correct facing/normals, lit material, and mesh collider. This scene is an asset integration preview, not a driving game.
5. Check Graphics and each Quality level: the URP asset should be assigned. Check Console for errors. Save, close, and reopen to verify persisted references.
6. Commit generated `ProjectSettings`, `Packages/packages-lock.json`, all content `.meta` files, generated URP/data/scene/prefab assets, and importer settings after review. Never commit `Library`, `Temp`, or other caches.

The C# scaffold and URP setup command have not been compiled or executed on the setup machine because Unity is not installed. Package compatibility and the preview must be verified here before calling milestone 0 fully engine-validated.

## Input and build dependencies

URP is the only non-module package in the initial manifest. Add the editor-recommended stable **Input System** package when implementing controls, select it as the active input handling backend, and commit both manifest and lock. Add Cinemachine if it improves the camera workflow, and Unity Test Framework when gameplay rule tests are introduced. No unneeded networking, analytics, or cloud packages are preinstalled.

Once the gameplay scenes exist, create desktop Build Profiles with `Bootstrap` first and all course scenes included. Put output in root `builds/`. For Windows development builds from Mac, install the matching Windows Mono build module. Use a Windows build machine with the required toolchain for Windows IL2CPP release builds. Pin build modules with the editor version. Add CI compilation and rule tests after local editor verification; runners need the appropriate Unity license.

## Version control rules

`.gitattributes` marks art binaries for LFS. Run `git lfs env` and `git lfs ls-files` to confirm LFS is active before a binary commit. On a fresh clone run `git lfs pull`. Source art and exports are both versioned; exports let gameplay contributors work without Blender.

Unity owns importer `.meta` files for FBX/textures. The seed supplies stable metadata for folders and C# files. Move Unity assets through the editor, preserving `.meta` GUIDs. Keep scenes, materials, definitions and prefabs in text form. No remote, commit, release, or hosted CI is configured by this setup.
