#!/bin/sh

fix_firmwareExe()
{
    if [ "$FILE_MD5" = "$1" ]; then
        printf '\x00\x00\x00\x00' | dd of=/usr/prog/PROGRAM/software/firmwareExe bs=1 seek=$2 conv=notrunc
        [ "$3" -ne 0 ] && printf '\x00\x10' | dd of=/usr/prog/PROGRAM/software/firmwareExe bs=1 seek=$3 conv=notrunc
    fi
}

# Fix firmwareExe video
if ! grep -q 'START=off' ${MOD_CONF}/mod_data/camera.conf; then
    mv /dev/video0 /dev/video67
fi

FILE_MD5=$(md5sum /usr/prog/PROGRAM/software/firmwareExe | cut -d' ' -f1)

fix_firmwareExe "50bce9af77fb537e2170087102785d4a" 6536157 0 # 1.9.9
fix_firmwareExe "2b92736aba576885378d5684d3370072" 6538044 0 # 1.9.9 Pro
fix_firmwareExe "a43f43d135106bf67de8a1b54fad396c" 2984192 0 # 2.0.0 Tiger
fix_firmwareExe "b36afd3cb11ae6b9ba3cc2f0d1e79267" 2985136 0 # 2.0.0 Pro Tiger
fix_firmwareExe "d6a0d7c31eb16e0520e25c67a8b6221a" 6681680 0 # 2.0.0
fix_firmwareExe "01c4480248a21fd33528ae0eeb38b5a5" 6683536 0 # 2.0.0 Pro

grep -q zmod_klipper_c5 /usr/data/zmod/klipper/.git/config || rm -rf /usr/data/zmod/klipper/
mkdir -p /usr/data/zmod/klipper/

if grep -q "klipper_c5 = 1" ${MOD_CONF}/mod_data/variables.cfg; then
    mount --bind /usr/data/zmod/zmod/.shell/klipperDaemon /usr/prog/klipper/klipperDaemon
fi
exit
