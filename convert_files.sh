rm -rf out/*

# Loop through each file in the example_files directory
for file in example_files/*; do
  # Check if it's a file
  if [[ -f "$file" ]]; then
    # Extract the filename without the directory and extension
    filename=$(basename -- "$file")
    name_no_ext="${filename%.*}"

    # Run the magic-pdf command
    magic-pdf -p "$file" -o "out/${name_no_ext}.md" -m ocr -l german

    # Print a message indicating the file was processed
    echo "Processed: $file -> out/${name_no_ext}.md"
  fi
done