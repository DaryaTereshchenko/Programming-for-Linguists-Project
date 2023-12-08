#!/bin/bash

# Set the path to your named entities file
named_entities_file="/Users/dariastetsenko/Desktop/pcl1/Carroll.txt"

# Directory containing chapter files
chapter_dir="/Users/dariastetsenko/Desktop/Carroll/chapters"

# Loop through each chapter file
for chapter_file in "$chapter_dir"/chapter_*.txt; do
    # Extract chapter number from the file name
    chapter_number=$(echo "$chapter_file" | grep -o -E '[0-9]+')

    # Use grep to find the named entities in the current chapter and output the results to a file
    grep -i -w -f "$named_entities_file" "$chapter_file" > "Chapter${chapter_number}_Entities.txt"
done