# How to create qcow2 images.
`VERSION` is exact routeros version number.

### Create disk image.
```
qemu-img create -f qcow2 routeros_VERSION.qcow2 64m
```

### Install routeros.
```
qemu-system-x86_64 \
    -m 64 \
    -hda routeros_VERSION.qcow2 \
    -net nic,model=virtio \
    -cdrom ISO_FILE.iso \
```

*   Install every package except `kvm`
*   Add `dhcp-client` on `ether1`
