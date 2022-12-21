#! /bin/bash

echo "Creating virtual environment, installing requirements and running app"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    # Create a virtual environment
    python3.9 -m venv venv

    # Activate the virtual environment
    source venv/bin/activate

    pip install --upgrade pip

    # Install the required packages from the requirements file
    pip install -r requirements.txt --use-pep517 | grep -v 'already satisfied'
    
    # Run the Flask app
    python3 app.py
else
  # Display an error message if Python is not found
  echo "Error: This program needs Python to run, to install check out https://www.python.org/downloads/"
fi
