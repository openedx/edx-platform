#!/bin/bash

# Function to run stylelint and handle violations
function run_stylelint() {
    # Define the limit of violations
    local violations_limit=0

    # Run stylelint and count the number of violations
    local num_violations
    num_violations=$(stylelint "**/*.scss" | grep -c "warning\|error")

    # Record the metric
    echo "$num_violations" > "$METRICS_DIR/stylelint"

    # Check if number of violations is greater than the limit
    if [ "$num_violations" -gt "$violations_limit" ]; then
        fail_quality "stylelint" "FAILURE: Stylelint failed with too many violations: ($num_violations).\nThe limit is $violations_limit."
    else
        write_junit_xml "stylelint"
    fi
}

# Function to fail the build quality
function fail_quality() {
    local tool=$1
    local message=$2
    echo "$message"
    exit 1
}

# Function to write JUnit XML (dummy function for this example)
function write_junit_xml() {
    local tool=$1
    echo "<testsuite name=\"$tool\" tests=\"1\" failures=\"0\" errors=\"0\"></testsuite>" > "$tool-results.xml"
}

# Set the METRICS_DIR environment variable (change as needed)
export METRICS_DIR="./metrics"

# Create the metrics directory if it doesn't exist
mkdir -p "$METRICS_DIR"

# Run the stylelint function
run_stylelint
