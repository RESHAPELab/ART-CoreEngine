#!/bin/bash

# unzip jabref-5.0-alpha.zip
unzip datamining.zip
mkdir -p output
mv datamining.pkl output/datamining.pkl
# git submodule update --init --recursive
