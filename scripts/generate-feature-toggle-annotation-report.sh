#!/usr/bin/env bash

# generate-feature-toggle-annotation-report.sh

# Generate a code annotations report for feature toggles in the platform.
# This script is part of the feature toggle generator tool.

pip install -r requirements/edx/paver.txt -r requirements/edx/testing.txt
rm -Rf reports/*
code_annotations static_find_annotations --config_file=../$CODE_ANNOTATION_CONFIG_PATH --no_lint
mkdir -p ../$CODE_ANNOTATION_OUTPUT_PATH
cp reports/* ../$CODE_ANNOTATION_OUTPUT_PATH/lms-annotations.yml
