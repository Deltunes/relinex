#!/bin/bash

echo "Initializing git submodules..."
git submodule update --init --recursive

conda env create -f env.yml
