#!/bin/sh

fix_firmwareExe()
{
    [ "$FILE_MD5" = "$1" ] && \
    printf '\x00\x00\x00\x00' | dd of=/usr/prog/PROGRAM/software/firmwareExe bs=1 seek=$2 conv=notrunc

}

# Fix firmwareExe video
if ! grep -q 'START=off' ${MOD_CONF}/mod_data/camera.conf; then
    mv /dev/video0 /dev/video67
fi

FILE_MD5=$(md5sum /usr/prog/PROGRAM/software/firmwareExe | cut -d' ' -f1)

fix_firmwareExe "50bce9af77fb537e2170087102785d4a" 6536157  # 1.9.9
fix_firmwareExe "2b92736aba576885378d5684d3370072" 6538044  # 1.9.9 Pro
fix_firmwareExe "a43f43d135106bf67de8a1b54fad396c" 2984192  # 2.0.0 Tiger
fix_firmwareExe "b36afd3cb11ae6b9ba3cc2f0d1e79267" 2985136  # 2.0.0 Pro Tiger
exit
