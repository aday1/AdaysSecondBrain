# Adays Second Brain - The Application!

## Overview
Welcome to what I use as a personal knowledge mental load management tool designed to help me track and manage anxiety-related data. While I do schema therapy, It allows me to log various metrics related to my anxiety, retrieve historical data, and monitor my mental health over time.

## Features
- **Log Anxiety Data**: I can save anxiety-related metrics such as SUDS score, isolation, unrelenting standards, and other indexes and develop coping strategies.
- **View Anxiety Logs**: Retrieve and view historical anxiety data in a structured format.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/aday1/AdaysSecondBrain.git
   cd AdaysSecondBrain
   ```

2. Set up !
   ```bash
   ./setup.sh
   ```

3. Install the required packages:
   ```bash
   install.sh
   ```

4. Initialize the database (if applicable):
   ```bash
   ./pkm.sh init-db
   ```

## Usage
1. Start the Flask application:
   ```bash
   pkm.sh web
   ```

2. The web application uses the following endpoints:
   - **POST /save_anxiety_data**: Save anxiety data by sending a JSON payload.
   - **GET /get_anxiety_data**: Retrieve all anxiety logs.
   - **GET /get_current_datetime**: Get the current date and time.
    You can see the endpoints in app.py

3. You can use pkm.sh to get into a console version (under development as well)

## Acknowledgments
- Flask for the web framework.
- SQLAlchemy for database management.
- Github / Claude etc