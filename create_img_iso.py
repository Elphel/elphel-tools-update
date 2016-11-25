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

# params
IMG_NAME = "sdimage.img"
ISO_NAME = "sdimage.iso"

SDCARD_SIZE = 3000

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

# functions
# useful link 1: http://superuser.com/questions/868117/layouting-a-disk-image-and-copying-files-into-it
# useful link 2: poky/scripts/contrib/mkefidisk.sh
# (?) useful link 3: http://unix.stackexchange.com/questions/53890/partitioning-disk-image-file

def shout(cmd):
    #subprocess.call prints to console
    subprocess.call(cmd,shell=True)

def create_empty_img(name,sizeM):
    #dd if=/dev/zero of=card.img bs=1M count=356
    shout("dd if=/dev/zero of="+name+" bs=1M count="+str(sizeM))

print("== Create image file: "+IMG_NAME)
if os.path.isfile(IMG_NAME):
  shout("rm -rf "+IMG_NAME)
  
create_empty_img(IMG_NAME,SDCARD_SIZE)

shout("parted "+IMG_NAME+" mktable "+PT_TYPE)

print("== Create partitions")
shout("parted "+IMG_NAME+" mkpart primary "+BOOT_FS+" 1 "+str(BOOT_SIZE))
shout("parted "+IMG_NAME+" mkpart primary "+ROOT_FS+" "+str(BOOT_SIZE+1)+" 100%")
# no need?
shout("parted "+IMG_NAME+" align-check optimal 1")
shout("parted "+IMG_NAME+" align-check optimal 2")

#kpartx
print("== kpartx create devices")
# Enables the kernel module requested by kpartx, just in case.
shout("modprobe dm-mod")

shout("kpartx -av "+IMG_NAME)

#wait for devices
devs_created = False
while not devs_created:
    if (os.path.exists("/dev/mapper/loop0p1")) and (os.path.exists("/dev/mapper/loop0p2")):
        devs_created = True
    else:
        print("waiting")
        time.sleep(0.5)

shout("mkfs.vfat /dev/mapper/loop0p1 -F 32 -n "+BOOT_LABEL)
shout("mkfs.ext4 /dev/mapper/loop0p2 -L "+ROOT_LABEL)

if not os.path.isdir("tmp"):
  shout("mkdir tmp")
else:
  shout("umount tmp")

print("== copy boot to /dev/mapper/loop0p1")
shout("mount /dev/mapper/loop0p1 tmp")
for i in BOOT_FILE_LIST:
    print("    "+i)
    shout("cp "+i+" tmp")
shout("umount tmp")

print("== copy rootfs to /dev/mapper/loop0p2")
shout("mount /dev/mapper/loop0p2 tmp")
shout("tar -C tmp/ -xzpf "+ROOT_ARCHIVE)
shout("umount tmp")

#sys.exit()

shout("rm -rf tmp")

#print("== convert img to iso")
#http://www.linuxquestions.org/questions/linux-software-2/how-to-convert-img-to-iso-files-325650/
#shout("mkisofs -f -r -udf -o "+ISO_NAME+" "+IMG_NAME)
#shout("dd if=/dev/loop0 of="+ISO_NAME)

print("== kpartx removes devices")
shout("kpartx -dv "+IMG_NAME)

print("== compress img")
shout("tar -czvf "+IMG_NAME+".tar.gz "+IMG_NAME)

#print("== compress iso")
#shout("tar -czvf "+ISO_NAME+".tar.gz "+ISO_NAME)

print("Done")
