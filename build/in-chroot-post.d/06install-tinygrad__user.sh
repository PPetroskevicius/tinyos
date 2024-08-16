#!/usr/bin/env bash
set -xeo pipefail

pushd /home/tiny

# clone tinygrad
git clone https://github.com/tinygrad/tinygrad tinygrad

pushd tinygrad

# checkout to specific version
git checkout 5f1554b5744ef5a0f4141a47a8e4d8196f96acb1

# install tinygrad and deps
pip install -e .[testing,linting,docs]
pip install pillow numpy tqdm

# symlink datasets and weights
ln -s /raid/datasets/imagenet extra/datasets/
ln -s /raid/weights ./

popd

popd
