# Delivery roadmap

| Milestone | Build | Acceptance gate |
| --- | --- | --- |
| 0 — Foundation (this setup) | Repository, engine decision, content types, asset pipeline, editor setup | Repo checks and Blender export run; Unity first-open verification remains pending |
| 1 — Driving playground | One kart, ground probes, throttle/brake, drift/boost, air control, chase camera, recovery | Controller and keyboard feel good on straight, bank, ramp, landing, grass, and wall; no speed tunneling |
| 2 — Visual benchmark | One finished kart/driver and a short finished road section | Coherent final-style materials, lighting, scenery and effects in a standalone build at race speed; baseline devices named and profiled |
| 2b — DIY console input spike | Existing phone system connected through the input adapter; one phone, one kart | Pair/reconnect on LAN, usable steering/buttons, stale-input stop, latency measured; keyboard still works |
| 3 — Canopy Rush blockout | Complete loop, checkpoints, laps, grid, boost/launch pads, grass, one moving hazard | Three laps finish reliably; missed checkpoints cannot cheat a lap; shortcuts have a tradeoff; safe respawns |
| 4 — Race and combat | Seven AI, four items, pickup spawning, placement, finish/results | AI completes repeated races and recovers; effects expire; hits communicate counterplay; stable frame times in an eight-kart fight |
| 5 — Finished vertical slice | Final course art, audio mix, UI, options, controller flow, build pipeline | A new player can launch, race, finish, and restart without the editor; art quality matches benchmark across the course |
| 6 — Local party mode and expansion | Multiple phone players, split-screen prototype, more courses and karts | Independent controller ownership, per-camera HUD, disconnect recovery, two-player frame budget; profile four players before committing |

## Next implementation task

Install the pinned Unity editor, run the setup command, inspect the ramp preview, and record the first clean package resolution. Then implement a controllable kart in `Scenes/Development/HandlingPlayground`, using primitives first and the same prefab structure planned for final Blender art.

Do not produce four finished tracks before proving driving feel and one finished visual segment. Do not add online services before the offline race loop is enjoyable and reliable.

The phone input spike is local controller transport, not online game networking. It is deliberately early because the DIY console is a confirmed product requirement.
