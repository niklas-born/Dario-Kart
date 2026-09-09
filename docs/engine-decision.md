# Engine and language decision

Decision date: 2026-09-08. Recommendation adopted for this foundation; revisit if the target platform or visual direction changes.

## Recommendation

Use **Unity 6.3 LTS, C#, URP, and Blender**. Pin editor **6000.3.23f1** as a reproducible starting point. It is a verified LTS patch, not a claim that it is the newest Unity release. Newer Update releases exist; we choose a supported LTS baseline to limit tooling churn while establishing the pipeline. Unity lists 6.3 LTS support through December 2027. [Support policy](https://unity.com/releases/unity-6/support), [pinned release](https://unity.com/releases/editor/whats-new/6000.3.23f1).

Blender authors meshes, rigs, animations, UVs, and baked textures. Unity runs the game: rendering, input, physics, audio, gameplay, UI, and builds. Modern Blender has no built-in game runtime; its original game engine was removed in 2.80. [Blender release notes](https://developer.blender.org/docs/release_notes/2.80/removed_features/).

## Comparison for this project

The iteration and complexity assessments below are engineering judgments for a small team building a stylized racer.

| Choice | Language / authoring | Strength for this game | Tradeoff | Decision |
| --- | --- | --- | --- | --- |
| Unity + URP | C#, Shader Graph | Fast gameplay tuning, reusable prefabs, broad deployment options, scalable rendering | We must deliberately build the lighting, materials, camera, and art style | Choose |
| Unreal Engine 5 | C++ for core systems; Blueprints for designer tuning; materials/Niagara for visuals | Strong environment, lighting, and effects workflows; attractive for a high-end PC/console focus | More editor/build complexity; Mac rendering features differ from Windows | Strong alternate |
| Unity + HDRP | C#, Shader Graph | High-end lighting for a narrowly targeted desktop game | Higher rendering cost and narrower platform scope than we need initially | Revisit only if art tests demand it |
| Blender alone | Python tools | Excellent asset authoring and offline rendering | Does not supply the supported game runtime this project needs | Use alongside Unity |
| Godot | GDScript / C# | Capable engine, but user wants another workflow | A switch back would not address the requested direction | Out of scope |
| Custom browser engine | TypeScript + WebGL/WebGPU | Instant link-based distribution | More custom tooling and game infrastructure to reach the intended scope | Reassess only if browser-first becomes mandatory |

URP provides a configurable rendering pipeline across platforms; it does not imply a low-poly or mobile-only art style. [Unity URP introduction](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/urp-introduction.html).

Unreal remains viable on Mac, but Epic lists hardware ray-traced Lumen as unsupported and Nanite/VSM support on M2+ as beta in its current requirements. Evaluate on actual target hardware before choosing those features as visual dependencies. [Epic macOS requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine).

## Visual quality comes from the pipeline

The previous Godot results do not establish an engine quality ceiling. Blender can improve models, silhouettes, UVs, and texture work; its Cycles renders do not transfer into real-time gameplay automatically. Validate assets in Unity under the intended lighting and race camera from the beginning.

Target a polished animated-film look: rounded forms, coherent palette, readable road edges, expressive drivers, layered scenery, strong lighting, and purposeful VFX. Use URP Lit first, baked environment lighting plus real-time kart shadows, reflection probes, controlled bloom, color grading, and measured anti-aliasing. Avoid high-frequency detail that becomes noise at racing speed. Build one art benchmark alongside the driving prototype, before producing a full course set.

## Language and systems

- C#: game simulation, race rules, items, camera, AI, UI, Unity editor tooling.
- Python: Blender export and asset validation tools only.
- Shader Graph: initial custom materials and effects; HLSL only when profiling or a concrete effect requires it.
- Begin with GameObjects and a custom arcade Rigidbody controller using ground probes. Simulation vehicle realism is not the goal; do not base the design on wheel friction tuning alone. Evaluate suspension and jump behavior in the first prototype.
- Defer DOTS/ECS, a networking stack, Addressables, and custom rendering until requirements justify them. Plan clean input and race-state boundaries now without claiming deterministic physics or multiplayer support.

## Licensing and operating cost

Unity currently offers Personal subject to its $200K financial eligibility rules; Pro is required above the relevant threshold. The Runtime Fee was canceled. Unreal's standard game license uses royalties above $1M lifetime gross product revenue, generally 5%, with exclusions and possible discounts. These are planning summaries; use the current terms at release. [Unity plans](https://unity.com/products), [Runtime Fee cancellation](https://unity.com/blog/unity-is-canceling-the-runtime-fee), [Unreal licensing](https://www.unrealengine.com/license).

No paid assets, engine subscriptions, online services, or third-party vehicle frameworks are required for the first slice. Console SDK access and platform-specific requirements are a separate future decision.
