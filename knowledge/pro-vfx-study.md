# What pro Roblox VFX actually do (study #1, Sep 28 2026)

Source: 6 free Creator Store packs inserted into `ServerStorage > VFX Study` of the Solar Verdict place
(Yona VFX Pack, Euphoric Games VFX PACK, AstricFox Massive Meshes, synmade VFX Pack, cchimpkinn Wind, nico_pi31 Auras).
645 ParticleEmitters, 911 MeshParts, 31 Beams. All 31 scripts were harmless spin/flicker loops and were removed.

## Numbers across all 645 emitters
| Setting | What pros use | What Solar Verdict v2 did |
|---|---|---|
| LightEmission | median **0.6** (0 for dark layers, 0.5-0.7 mid, 1 only for glow) | 1 on almost everything, hence the white blowout |
| Brightness | median **2** | 2-6 |
| LightInfluence | 0 on 88% | 0 |
| Lifetime | median **0.7 s** | 0.35-2.4 s |
| Speed | median **0**: most layers don't move; the size curve animates them | everything flies |
| LockedToPart | **56%** | none |
| ZOffset | set on **64%** (layer ordering) | rarely |
| Rotation | random on **77%**, RotSpeed on 42% | some |
| Flipbooks | **35%**, mostly Grid4x4 | 3 emitters |
| Transparency | 3+ keypoints on 58%, fade-in envelope on 45% | 2 keypoints |
| Size | 0 -> peak at ~0.25 -> 0 is the signature pop | linear |
| Color | 2 keypoints on 98%: the texture carries the look, not the gradient | gradients |
| Orientation | FacingCamera 64%, VelocityPerpendicular 20% (flat rings), VelocityParallel 15% (streaks) | mostly FacingCamera |
| Attributes | **EmitCount** on 320, **EmitDelay** on 160, EmitDuration on 8 | none |

## Techniques seen in a real explosion (Yona "Explosion-02", 23 emitters)
1. **Dark layers for contrast.** 6 of 23 emitters are black (`Color 0,0,0`, `LightEmission 0`): dark specks, dark shards, dark smoke. Bright reads as bright only next to dark.
2. **Blast then snap stop.** Shards and specks: Speed 140-280 with **Drag 7-10**. They explode out and freeze, with no floaty drift.
3. **Pop curve.** Size 0 -> peak at 0.25 of life -> 0. Particles appear, punch, and vanish.
4. **One huge flipbook, not many small ones.** Fire = 3 variants of a 4x4 flipbook, EmitCount 1 each, Size 25, rotation random. Transparency holds at 0 until ~70% of life, then drops fast (crisp, not mushy).
5. **Spinning flat slash rings.** WindSlash: VelocityPerpendicular, RotSpeed 400-600, size 8 -> 23, fade in then out.
6. **Hot streak lines.** Lines2: VelocityParallel, Brightness 10, orange, 5-key transparency envelope.
7. **Layer sorting with ZOffset** (0 to 9) so dark shards sit in front of fire and wind sits on top.

## Mesh packs
Shape is everything: Neon meshes (slashes, spirals, tornadoes, shockwave domes, wind wraps) animated by scaling/rotating, rarely textured.
Useful public mesh ids (from synmade pack): slash 4572036304, Slash_Skill1 452960473, spiral 6092662636 / 903178515,
tornado 5705014362, wind wraps 6553031952 / 6553036976 / 6553119537, swirl 6553284529, shockwave domes 5694662220 / 5697180395,
wave rings 4901270068 / 2689837482, ring 1851169338, ground spikes 967645205, spiky ball 3375161112.

## Reusable pro textures (public, from the packs)
shard streak 10439119562, specs 9997556038 / 8030760338 / 10632727506, smoke 10180479311 / 9232117588,
hot lines 9145574991, streak 6763809313, rock 8132607319, wind ring 10176632695, wind slash 8101328122,
fire flipbooks 4x4: 11395089850 / 11395090403 / 11395118687.

## Rules to apply from now on
- Give every emitter `EmitCount` (+ `EmitDelay` when it fires late). That's how VFX Suite style emitter plugins read and preview it.
- At least 25% of an impact's layers should be **dark** (black, LightEmission 0).
- Bursts: high Speed + Drag 7-10, pop size curve, lifetime 0.3-0.8.
- LightEmission 1 only on the glow/core layers; everything else 0.5-0.7 with Brightness around 2.
- Big hero sprites: one large flipbook, held opaque, fast fade at the end.
- Use ZOffset deliberately to stack layers.
- Prefer meshes for slashes, spirals, shockwaves; particles for specks, smoke, sparks.
