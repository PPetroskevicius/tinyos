help:
	@echo "make red"
	@echo "       build tinyos.red.img for tinybox red"
	@echo "make green"
	@echo "       build tinyos.green.img for tinybox green"
	@echo "make clean"
	@echo "       clean up"

clean:
	rm -f tinyos.yaml build/tinybox-release
	mountpoint -q result/chroot/proc && sudo umount result/chroot/proc
	mountpoint -q result/chroot/sys && sudo umount result/chroot/sys
	mountpoint -q result/chroot/dev/pts && sudo umount result/chroot/dev/pts
	mountpoint -q result/chroot/dev && sudo umount result/chroot/dev
	sudo rm -rf result

red:
	sed 's/<|ARTIFACT_NAME|>/tinyos.red.img/g' tinyos.template.yaml > tinyos.yaml
	echo "TINYBOX_COLOR=red" | tee --append build/tinybox-release
	time make image

green:
	sed 's/<|ARTIFACT_NAME|>/tinyos.green.img/g' tinyos.template.yaml > tinyos.yaml
	echo "TINYBOX_COLOR=green" | tee --append build/tinybox-release
	time make image

image:
	sudo ubuntu-image classic --debug -w result -u perform_manual_customization tinyos.yaml
	sudo mkdir -p result/chroot/proc result/chroot/sys result/chroot/dev/pts
	sudo mount -t proc none result/chroot/proc
	sudo mount -t sysfs none result/chroot/sys
	sudo mount -o bind /dev result/chroot/dev
	sudo mount -t devpts none result/chroot/dev/pts
	sudo ubuntu-image classic --debug -w result -r -t perform_manual_customization tinyos.yaml
	sudo umount result/chroot/proc result/chroot/sys result/chroot/dev/pts result/chroot/dev
	sudo ubuntu-image classic --debug -w result -r tinyos.yaml
	rm -f tinyos.yaml build/tinybox-release

.PHONY: clean red green image
