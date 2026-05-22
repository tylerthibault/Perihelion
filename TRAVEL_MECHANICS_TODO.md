# Travel Mechanics Todo

## Summary
Track implementation work for complex travel, orbital movement, landing, docking, fuel, and stranding mechanics.

First gameplay pass is implemented: the ship now has travel states, local movement previews, planet flight stats, fuel/time/risk costs, jump blocking, rescue refuel, and tests.

## Travel State Model
- [x] Add explicit player location states: `deep_space`, `system_space`, `orbit`, `atmosphere`, `landed`, `docked`.
- [x] Track what body/location the ship is near: system, station, planet, or planet place.
- [x] Only allow interstellar jumps from `system_space` or `deep_space`.
- [x] Require ascent before jumping if landed, in atmosphere, docked, or orbiting.

## Procedural Planet Flight Stats
- [x] Generate planet size, mass, gravity, atmosphere density, and landing difficulty procedurally.
- [x] Make these values deterministic from planet seed so they remain stable.
- [x] Show gravity/atmosphere data in planet detail panels.
- [x] Use gravity and atmosphere to calculate ascent/descent fuel costs.

## Local Movement Costs
- [x] Add low-cost movement between system space and space stations.
- [x] Add medium-cost movement between station and planetary orbit.
- [x] Add high-cost descent/ascent between orbit and planet surface.
- [x] Add time costs for each movement type.
- [x] Add route previews before committing fuel.

## Detailed Orbital Travel
- [ ] Add orbital transfer phases between system space, station orbit, planetary orbit, and surface.
- [x] Add different cost formulas for docking, undocking, descent, ascent, and interstellar jumps.
- [x] Make large/high-gravity planets noticeably expensive to leave.
- [x] Make thin/no-atmosphere worlds cheaper to land on than dense-atmosphere worlds.
- [ ] Add a distinct station-orbit phase if we want stations to be separate from direct docking.

## Fuel and Stranding
- [x] Block travel if fuel is insufficient by default.
- [ ] Offer risky under-fueled travel as an explicit player choice.
- [x] Add rescue refueling options: fuel ship in space, fuel truck/service on planet surface.
- [x] Add rescue costs, delays, and possible debt/faction consequences.
- [ ] Add emergency outcomes for risky attempts: hull damage, delay, failed ascent, forced landing, or distress beacon.
- [ ] Expose risky under-fueled attempts in the UI instead of keeping them backend-only.

## UI / Player Clarity
- [x] Show current travel state in the top status bar.
- [x] Add movement options based on current state: `Undock`, `Enter orbit`, `Land`, `Launch`, `Jump`.
- [x] Show fuel/time/risk preview before committing movement.
- [x] Explain why unavailable moves are blocked.
- [x] Add warnings for high-gravity launches and low-fuel situations.

## Tests To Add Later
- [x] Cannot jump while landed/docked/orbiting.
- [x] Can jump only from system/deep space.
- [x] Planet gravity changes ascent fuel cost.
- [x] Atmosphere changes descent/ascent difficulty.
- [x] Rescue refuel works in space and on planet surface.
- [ ] Risky under-fueled travel can damage hull or fail.
- [x] Procedural planet travel stats are deterministic.

## Assumptions
- Use a detailed but game-friendly orbital state machine, not real orbital physics.
- All planet gravity/size/atmosphere stats will be procedural and deterministic.
- Stranding behavior will combine three modes: block first, then offer risky travel or paid rescue.
- The new file is a standalone checklist; existing gameplay todo files remain unchanged.
