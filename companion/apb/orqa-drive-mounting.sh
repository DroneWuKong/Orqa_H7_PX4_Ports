#!/bin/sh
# Only the SD path is replaced. Keep the vendor's USB behavior unchanged.
if [ "$1" = sdcard ]; then
    exec /usr/bin/python3 /usr/local/lib/orqa-px4/mount_sd.py "$2"
fi
exec /bin/sh /etc/udev/scripts/orqa-drive-mounting.sh.pre-px4-logging "$@"
