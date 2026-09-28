#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 /path/to/betaflight" >&2
    exit 64
fi

betaflight_root=$(CDPATH= cd -- "$1" && pwd)
config_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
nm_bin=${ARM_NONE_EABI_NM:-arm-none-eabi-nm}

if ! command -v "$nm_bin" >/dev/null 2>&1; then
    echo "error: $nm_bin is not available; set ARM_NONE_EABI_NM to the toolchain binary" >&2
    exit 69
fi

required_symbols=(
    gpsRescueIsConfigured
    initPositionHold
    updatePosHold
    pgResetTemplate_altHoldConfig
)

for target in ORQA_H743 ORQA_APB; do
    echo "building $target"
    make -C "$betaflight_root" \
        CONFIG="$target" \
        BETAFLIGHT_CONFIG="$config_root" \
        EXTRA_FLAGS="${EXTRA_FLAGS:--Werror}"

    elf="$betaflight_root/obj/main/betaflight_STM32H743_${target}.elf"
    if [[ ! -f "$elf" ]]; then
        echo "error: expected ELF was not produced: $elf" >&2
        exit 1
    fi

    symbols=$($nm_bin --defined-only "$elf" | awk '{ print $3 }')
    for symbol in "${required_symbols[@]}"; do
        if ! grep -Fqx "$symbol" <<<"$symbols"; then
            echo "error: $target is missing required GPS Rescue symbol: $symbol" >&2
            exit 1
        fi
    done

    echo "$target: GPS Rescue, altitude hold, and position hold are linked"
done
