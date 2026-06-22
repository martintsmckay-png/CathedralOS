#!/bin/bash
echo "Initiating Garden Hill Site Survey..."
echo "Timestamp: $(date)"
echo "Logging GPS: $2"
echo "Chalk marker: $4"
echo "Survey logged to marrow."
# This will eventually save to a file
date +%s > ~/cathedral-os/marrow/survey_$(date +%s).ritual

