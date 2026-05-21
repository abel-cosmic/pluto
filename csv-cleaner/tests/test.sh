#!/bin/bash

# Create logs directory
mkdir -p /logs/verifier

# Run tests in an isolated pytest environment using uvx
if uvx pytest /tests/test_csv.py -v; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
