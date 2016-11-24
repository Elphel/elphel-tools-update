#!/usr/bin/env python
'''
# Copyright (C) 2016, Elphel.inc.
# Usage: known
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.

@author:     Oleg K Dzhimiev
@copyright:  2016 Elphel, Inc.
@license:    GPLv3.0+
@contact:    oleg@elphel.com
@deffield    updated: unknown

'''

__author__ = "Elphel"
__copyright__ = "Copyright 2016, Elphel, Inc."
__license__ = "GPL"
__version__ = "3.0+"
__maintainer__ = "Oleg K Dzhimiev"
__email__ = "oleg@elphel.com"
__status__ = "Development"

import subprocess
import sys
import os
import time

# functions
# useful link 1: http://superuser.com/questions/868117/layouting-a-disk-image-and-copying-files-into-it
# useful link 2: poky/scripts/contrib/mkefidisk.sh
# (?) useful link 3: http://unix.stackexchange.com/questions/53890/partitioning-disk-image-file

def shout(cmd):
    #subprocess.call prints to console
    subprocess.call(cmd,shell=True)
def print_help():
    print("\nDesctiption:\n")
    print("  * Required programs: kpartx")
    print("  * Run under superuser. Make sure the correct device is provided.")
    print("  * Erases partition table on the provided device")
    print("  * If given someimage.img file - burns the sd card from it")
    print("  * If not - uses the files from the predefined list")
    print("  * Creates FAT32 partition labeled 'BOOT' and copies files required for boot")
    print("  * Creates EXT4 partition labeled 'root' and extracts rootfs.tar.gz")
    print("\nExamples:\n")
    print("  * Use files (names are hardcoded) from the current dir ('build/tmp/deploy/images/elphel393/mmc/'):")
    print("      ~$ python make_sdcard.py /dev/sdz")
    print("  * Use someimage.img file:")
    print("      ~$ python make_sdcard.py /dev/sdz someimage.img")
    print("  * To write *.iso use a standard os tool that burns bootable USB drives")
    print("")
    
if len(sys.argv) > 1:
    DEVICE = sys.argv[1]
else:
    DEVICE = ""
    print_help()
    sys.exit()

if len(sys.argv) > 2:
    IMAGE_FILE = sys.argv[2]
    if not IMAGE_FILE.endswith(".img"):
        print("ERROR: Please, provide *.img file or leave argument empty to use certain image files in the current dir")
        sys.exit()
else:
    IMAGE_FILE = ""


#params
SDCARD_SIZE = 4000

PT_TYPE = "msdos"

BOOT_LABEL = "BOOT"
BOOT_FS = "fat32"
BOOT_SIZE = 128
BOOT_FILE_LIST = (
    "boot.bin",
    "u-boot-dtb.img",
    "devicetree.dtb",
    "uImage"
    )

ROOT_LABEL = "root"
ROOT_FS = "ext4"
ROOT_ARCHIVE = "rootfs.tar.gz"

something_is_missing = False

if IMAGE_FILE=="":
    print("Preparing SD card using files: "+str(BOOT_FILE_LIST + (ROOT_ARCHIVE,)))
    for f in BOOT_FILE_LIST + (ROOT_ARCHIVE,):
        if not os.path.isfile(f):
            print("file "+f+" is missing")
            something_is_missing = True
else:
    print("Preparing SD card from "+IMAGE_FILE)
    if not os.path.isfile(IMAGE_FILE):
        print("No such file")
        something_is_missing = True

if not os.path.exists(DEVICE):
    print("No such device")
    something_is_missing = True

if something_is_missing:
    sys.exit()

print("= Erase partition table on "+DEVICE)
shout("dd if=/dev/zero of="+DEVICE+" bs=512 count=2048")

print("= Create partition table")
shout("parted -s "+DEVICE+" mktable "+PT_TYPE)

print("= Create FAT32 parttion")
shout("parted -s "+DEVICE+" mkpart primary "+BOOT_FS+" 1 "+str(BOOT_SIZE))
shout("parted -s "+DEVICE+" mkpart primary "+ROOT_FS+" "+str(BOOT_SIZE+1)+" 100%")
# no need?
shout("parted -s "+DEVICE+" align-check optimal 1")
shout("parted -s "+DEVICE+" align-check optimal 2")

devs_created = False
while not devs_created:
    if (os.path.exists(DEVICE+"1")) and (os.path.exists(DEVICE+"2")):
        devs_created = True
    else:
        print("waiting")
        time.sleep(0.5)

time.sleep(1)
print("= Format")

shout("mkfs.vfat "+DEVICE+"1 -F 32 -n "+BOOT_LABEL)
shout("mkfs.ext4 "+DEVICE+"2 -F -L "+ROOT_LABEL)

shout("mkdir tmp")

if IMAGE_FILE=="":
    shout("mount "+DEVICE+"1 tmp")
    for i in BOOT_FILE_LIST:
        print("    "+i)
        shout("cp "+i+" tmp")
    shout("umount tmp")

    shout("mount "+DEVICE+"2 tmp")
    shout("tar -C tmp/ -xzpf "+ROOT_ARCHIVE)
    shout("umount tmp")
else:
    shout("modprobe dm-mod")
    shout("kpartx -av "+IMAGE_FILE)
    
    #wait for devices
    devs_created = False
    while not devs_created:
        if (os.path.exists("/dev/mapper/loop0p1")) and (os.path.exists("/dev/mapper/loop0p2")):
            devs_created = True
        else:
            print("waiting")
            time.sleep(0.5)
    
    shout("mkdir tmp2")
    
    shout("mount "+DEVICE+"1 tmp")
    shout("mount /dev/mapper/loop0p1 tmp2")
    shout("rsync -a tmp2/ tmp")
    shout("umount tmp")
    shout("umount tmp2")
    
    shout("mount "+DEVICE+"2 tmp")
    shout("mount /dev/mapper/loop0p2 tmp2")
    shout("rsync -a tmp2/ tmp")    
    shout("umount tmp")
    shout("umount tmp2")
    
    shout("rm -rf tmp2")
    
    shout("kpartx -dv "+IMAGE_FILE)

shout("rm -rf tmp")

print("Done")
