# Phase 1: Scaffold and Build - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a reproducible build environment and a clean-compiling PX4 board target for `orqa/h7quadcore`. Developer can produce a `.px4` firmware binary with a single command and flash it to the physical board via DFU. No sensor bring-up in this phase.

</domain>

<decisions>
## Implementation Decisions

### Repository strategy
- Local branch on a cloned PX4-Autopilot — no GitHub fork yet (fork deferred until upstream PR time)
- Pin to a stable release tag (e.g. v1.15.x), not main
- Board target lives in-tree: `boards/orqa/h7quadcore/`
- This project directory and PX4-Autopilot clone live as sibling directories (separate repos, no nesting)

### Build invocation
- Shell script wrapper (`build.sh`) at this project root
- Single command invokes `docker run` targeting the pinned px4io image and building `px4_orqa_h7quadcore`
- No local compiler required — Docker only

### Base target
- Derive from Matek H743 Slim (same STM32H743 MCU family, community-proven PX4 port)
- Already decided in PROJECT.md — Claude has discretion on whether to copy wholesale or adapt incrementally

### Flash procedure
- dfu-util via boot button (meets BUILD-03 success criterion)
- Claude's discretion on whether to include STM32CubeProgrammer as documented fallback

### Claude's Discretion
- Which exact px4io Docker image tag to pin
- Whether to copy Matek H743 Slim files wholesale or build incrementally
- STM32CubeProgrammer as optional fallback for flashing
- CMake/nuttx config details within the board target

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Build must be a single Docker command producing a `.px4` binary; flash must use DFU mode via boot button.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.zip`: Contains full pin/timer/DMA assignments — primary reference for all GPIO mapping in the board target
- Orqa H7 QuadCore User Manual v1.1: Hardware reference for board schematic details

### Established Patterns
- No PX4 source code exists yet in this project — this phase creates it
- Matek H743 Slim board target in PX4-Autopilot (`boards/matek/h743-slim/`) is the direct reference implementation

### Integration Points
- Board target output (`.px4` binary) feeds into Phase 2 (sensor bring-up requires a flashable firmware)
- DFU flash procedure documented here becomes the standard workflow for all subsequent phases

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-scaffold-and-build*
*Context gathered: 2026-03-10*
