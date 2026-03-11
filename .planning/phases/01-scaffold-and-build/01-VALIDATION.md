---
phase: 1
slug: scaffold-and-build
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None applicable — firmware compilation, not unit tests |
| **Config file** | none — Wave 0 creates `build.sh` and board target |
| **Quick run command** | `./build.sh` |
| **Full suite command** | `./build.sh 2>&1 \| grep -E "error:\|warning:" \| wc -l` (should output `0`) |
| **Estimated runtime** | ~3-5 minutes (Docker build) |

---

## Sampling Rate

- **After every task commit:** Run `./build.sh`
- **After every plan wave:** Run full build + manual DFU smoke test on hardware
- **Before `/gsd:verify-work`:** Full build green + physical board boots to DFU mode
- **Max feedback latency:** ~5 minutes (Docker build time — unavoidable for embedded firmware)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | BUILD-01, BUILD-02 | smoke | `./build.sh` | ❌ Wave 0 | ⬜ pending |
| 1-01-02 | 01 | 1 | BUILD-01 | smoke | `./build.sh` exits 0 | ❌ Wave 0 | ⬜ pending |
| 1-01-03 | 01 | 1 | BUILD-02 | smoke | `./build.sh 2>&1 \| grep -cE "error:\|warning:"` → `0` | ❌ Wave 0 | ⬜ pending |
| 1-01-04 | 01 | 2 | BUILD-03 | manual | Hold BOOT + plug USB; `dfu-util -l` shows `[0483:df11]`; flash bootloader; flash firmware via QGC | N/A — hardware | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `../PX4-Autopilot/boards/orqa/h7quadcore/` — entire board target directory tree (does not exist yet)
- [ ] `build.sh` — Docker wrapper script (does not exist yet)
- [ ] Board target must be created before any build command can be validated

*Wave 0 must create all artifacts before automated verification is possible.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DFU flash succeeds and firmware boots | BUILD-03 | Requires physical hardware: Orqa H7 QuadCore board, USB-C cable, host `dfu-util` install | 1. Hold BOOT button, plug USB-C → run `dfu-util -l` → confirm `[0483:df11]`. 2. Flash PX4 NuttX bootloader `.bin` to `0x08000000`. 3. Unplug/replug. 4. Flash `.px4` firmware via QGroundControl or `make upload`. 5. Board should enumerate as PX4 flight controller. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 360s (5 min Docker build)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
