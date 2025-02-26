#!/usr/bin/env bash
set -xeo pipefail

source /etc/tinybox-release

if [[ "$TINYBOX_COLOR" == "red" ]]; then
  # https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/install-methods/package-manager/package-manager-ubuntu.html
  # Make the directory if it doesn't exist yet.
  # This location is recommended by the distribution maintainers.
  sudo mkdir --parents --mode=0755 /etc/apt/keyrings

  # Download the key, convert the signing-key to a full
  # keyring required by apt and store in the keyring directory
  wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null

  # register kernel-mode driver
  echo "deb [arch=amd64,i386 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/amdgpu/6.3.3/ubuntu noble main" | sudo tee /etc/apt/sources.list.d/amdgpu.list
  sudo apt update -y

  # register ROCm packages
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.3.3 noble main" \
    | sudo tee --append /etc/apt/sources.list.d/rocm.list
  echo -e 'Package: *\nPin: release o=repo.radeon.com\nPin-Priority: 600' \
    | sudo tee /etc/apt/preferences.d/rocm-pin-600
  sudo apt update -y

  # install kernel driver and ROCm packages
  apt install amdgpu-dkms rocm rocm-bandwidth-test -y
elif [[ "$TINYBOX_COLOR" == "green" ]]; then
  pushd /tmp

  curl -o keyring.deb -L "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb"
  dpkg -i keyring.deb

  curl -o driver.deb -L "https://github.com/tinygrad/open-gpu-kernel-modules/releases/download/550.90.07-p2p/nvidia-kernel-source-550-open-0ubuntu1_amd64.deb"
  dpkg -i driver.deb

  apt update -y
  apt install cuda-toolkit-12-4 nvidia-driver-550-open cuda-drivers-550 -y

  # hold the nvidia driver
  apt-mark hold nvidia-driver-550-open nvidia-dkms-550-open nvidia-kernel-common-550 nvidia-kernel-source-550-open cuda-drivers-550 cuda-toolkit-12-4 libnvidia-common-550
  popd
elif [[ "$TINYBOX_COLOR" == "blue" ]]; then
  wget -qO - https://repositories.intel.com/gpu/intel-graphics.key | gpg --yes --dearmor --output /usr/share/keyrings/intel-graphics.gpg
  wget -qO - https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --yes --dearmor --output /usr/share/keyrings/oneapi-archive-keyring.gpg

  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy/lts/2350 unified" | tee /etc/apt/sources.list.d/intel-graphics-jammy.list
  echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | sudo tee /etc/apt/sources.list.d/oneAPI.list

  # install intel drivers and mesa
  apt update -y
  apt install "linux-headers-$(uname -r)" "linux-modules-extra-$(uname -r)" -y
  apt install flex bison -y
  apt install intel-fw-gpu xpu-smi -y # out-of-tree: intel-i915-dkms
  apt install intel-opencl-icd intel-level-zero-gpu level-zero intel-media-va-driver-non-free -y
  apt install libmfx1 libmfxgen1 libvpl2 libegl-mesa0 libegl1-mesa libegl1-mesa-dev libgbm1 libgl1-mesa-dev libgl1-mesa-dri libglapi-mesa libgles2-mesa-dev libglx-mesa0 libigdgmm12 libxatracker2 -y
  apt install mesa-va-drivers mesa-vdpau-drivers mesa-vulkan-drivers va-driver-all -y
  apt install vainfo hwinfo clinfo -y
  apt install libigc-dev intel-igc-cm libigdfcl-dev libigfxcmrt-dev level-zero-dev -y

  # install oneAPI
  apt install intel-basekit -y
else
  echo "Unknown tinybox color: $TINYBOX_COLOR"
  exit 1
fi
