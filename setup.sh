#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# Initialize the database
python pkm/init_db.py

echo "Setup completed successfully."
