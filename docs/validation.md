# Foundation validation

Checked on 2026-09-08 on the setup Mac.

| Check | Result |
| --- | --- |
| Git initialization | Initialized local `main`; no commit or remote configured |
| Blender source generation | Passed in installed Blender 5.2.1 LTS |
| Static FBX export | Passed; one original ramp mesh exported with provenance hashes |
| FBX binary header | Passed |
| Repository structure, JSON, metadata GUIDs, export source/output hashes | Passed using `python3 tools/check_repo.py` |
| Python source syntax | Passed using Python AST parsing |
| Relative Markdown file links | Passed |
| Unity package resolution and C# compilation | Pending: Unity editor not installed |
| Unity setup command, prefab references, import scale, renderer, preview | Pending: Unity editor not installed |
| Mac / Windows executable build | Pending: gameplay not implemented and editor/modules not installed |
| Driving, race rules, visuals, phone transport, frame rate | Not implemented / not measured |
| Git LFS binary tracking | Attributes configured; LFS installation still required before binary commit |

Blender background execution initially crashed inside the workspace sandbox; source generation and export succeeded outside it with approval. No Unity test result or visual-quality claim is inferred from the Blender export succeeding.

The next verification step is the [first Unity open](setup.md), followed by the driving playground milestone. Update this record after actual editor/build validation.
