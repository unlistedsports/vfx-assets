# Uploaded on reallydrawn (decal id -> image id used in Roblox)

| Texture | Decal ID | Image ID |
|---|---|---|
| flame_8x8 | 82101759152516 | 116335304553196 |
| electric_4x4 | 73041439399143 | 101457718545840 |
| spark_streak | 103385556757534 | 99537660436012 |
| soft_glow | 87175538242739 | 77567390774588 |
| star_glint | 106848097248032 | 135651278435848 |
| shock_ring | 99947628147989 | 116116033362655 |
| sigil_hd | 114043893779421 | 98238406476430 |
| impact_cracks | 129687976287030 | 77910263040610 |
| beam_scroll | 76595653526175 | 104723266600659 |
| smoke_8x8 | - | 112094987729177 |
| ground_scorch | - | 73512981979770 |

Decal ID -> image ID: `InsertService:LoadAsset(decalId)` in Studio, read the Decal's Texture.

## Status (Sep 28)
- All 9 load in personalfund's game after adding personalfund as a collaborator on the **Image** assets (not the Decals).
- `ContentProvider:PreloadAsync` wrongly reports Failure for these; test with an ImageLabel's `IsLoaded` instead.
- Extra public texture in use: Creator Store "Light Rays" image 101267161684975 (burst rays).
