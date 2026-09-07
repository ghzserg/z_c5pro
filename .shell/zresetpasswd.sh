#!/bin/sh
# (C) 2024-2026 ghzserg https://github.com/ghzserg/zmod

if [ -f /ZMOD ]; then
    /usr/data/zmod/zmod/.shell/zremote.sh /usr/data/zmod/zmod/.shell/zresetpasswd.sh
else
    yes root | passwd
    echo "New password: root"

    source /usr/data/zmod/zmod/.shell/0.sh
    if [ ${C5PRO} -eq 1 ] || [ ${AD5X} -eq 1 ]; then
        source /usr/data/zmod/zmod/.shell/activate.sh
        enable_zmod_ad5x_c5pro
    fi
fi
