#! /bin/bash

echo "Creating virtual environment, installing requirements and running game"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    # Create a virtual environment
    python3 -m venv venv

    # Activate the virtual environment
    source venv/bin/activate

    pip install --upgrade pip

    # Install the required packages from the requirements file
    # pip install -r requirements.txt --use-pep517 | grep -v 'already satisfied'
    pip install -r requirements.txt | grep -v 'already satisfied'
    
    # Run the Flask app
    python3 app.py
    # FLASK_APP=app.py flask run &

    sleep 2
    # Open the app in a browse
    open http://127.0.0.1:8080
else
  # Display an error message if Python is not found
  echo "Error: This program needs Python to run, to install check out https://www.python.org/downloads/"
fi