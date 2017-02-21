# How to create qcow2 images.
`VERSION` is exact routeros version number.

### Create disk image.
```
qemu-img create -f qcow2 routeros_VERSION.qcow2 64m
```

### Install routeros.
```
qemu-system-i386 \
    -m 64 \
    -hda routeros_VERSION.qcow2 \
    -net nic,model=e1000 \
    -cdrom ISO_FILE.iso \
    -vnc :3
```
Install every package except:
- kvm
