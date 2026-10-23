### AnyKernel3 Ramdisk Mod Script
## Cogan Kernel · Xiaomi 14T Pro (rothko) · github.com/cogan17/Xiomi_14T_Pro
## Only the kernel in boot changes: split_boot + flash_boot keep the phone's boot header and
## ramdisk; vendor_boot, init_boot, vbmeta and dtbo are never touched.

### AnyKernel setup
# global properties
properties() { '
kernel.string=KERNEL_STRING
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=rothko
device.name2=
supported.versions=
supported.patchlevels=
supported.vendorpatchlevels=
'; } # end properties


### AnyKernel install
# boot shell variables
BLOCK=boot;
IS_SLOT_DEVICE=auto;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;

# import functions/variables and setup patching - see for reference (DO NOT REMOVE)
. tools/ak3-core.sh;

ui_print " " "Cogan Kernel by Cogan (cogan17)" "FEATURES_LINE";
ui_print "Credits: Google ACK, KernelSU Next (rifsxd)," "pershoot, BakaSU, SUSFS (simonpunk)," "NoMount (maxsteeel), Baseband Guard," "AnyKernel3 (osm0sis)" " ";

# boot install
split_boot; # kernel only: the phone's ramdisk stays as it is
flash_boot;
## end boot install
