#!/bin/bash

# unzip jabref-5.0-alpha.zip
unzip datamining.zip
mkdir -p generatedFiles
mv datamining.pkl generatedFiles/datamining.pkl
git submodule init
git submodule update
