#!/usr/bin/env python3
"""
PKM Manager Module

This module provides the core functionality for the Personal Knowledge Management (PKM) system.
It handles all database operations, file management, and logging functions.

Key Features:
- Daily log creation and management
- Metrics tracking (mood, energy, sleep)
- Habit tracking
- Work logging
- Alcohol consumption tracking
- Database management and statistics

Usage:
    manager = PKMManager()
    
    # Create daily log
    manager.create_daily_log()
    
    # Log metrics
    manager.log_daily_metrics(mood=8, energy=7, sleep_hours=7.5)
    
    # Log habits
    manager.log_habit("Exercise")
    
    # Log work
    manager.log_work_hours_direct(hours=4, project="PKM Development")
"""

import sqlite3
import os
from datetime import datetime
import shutil

class PKMManager:
    """
    Main manager class for the PKM system.
    
    Handles all core operations including:
    - File management (daily logs, templates)
    - Database operations (metrics, habits, work logs)
    - Data retrieval and statistics
    
    Attributes:
        base_dir (str): Project root directory
        db_path (str): Path to SQLite database
        templates_dir (str): Path to template files
        daily_dir (str): Path to daily log files
    """
    
    def __init__(self):
        # Get the project root directory (one level up from pkm directory)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Update the db_path to use the correct location
        self.db_path = os.path.join(self.base_dir, 'pkm', 'db', 'pkm.db')
        self.templates_dir = os.path.join(self.base_dir, 'pkm', 'templates')
        self.daily_dir = os.path.join(self.base_dir, 'daily')
        
    def get_db_connection(self):
        """
        Create and return a database connection.
        
        Returns:
            sqlite3.Connection: Connection to the SQLite database
            
        Note:
            Caller is responsible for closing the connection
        """
        return sqlite3.connect(self.db_path)

    def check_database(self):
        """
        Verify database exists and has all required tables.
        
        Raises:
            Exception: If database is missing or incomplete
            
        Required Tables:
            - daily_metrics: Daily mood, energy, and sleep tracking
            - sub_daily_moods: Mood tracking throughout the day
            - habits: Habit definitions
            - habit_logs: Habit completion tracking
            - alcohol_logs: Alcohol consumption tracking
            - work_logs: Work hours and project tracking
            - goals: Goal tracking and management
        """
        required_tables = [
            'daily_metrics',
            'sub_daily_moods',
            'habits',
            'habit_logs',
            'alcohol_logs',
            'work_logs',
            'goals'
        ]
        
        if not os.path.exists(self.db_path):
            raise Exception("Database not found. Please run './pkm.sh init-db' to initialize the database.")
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get list of existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Check for missing tables
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                raise Exception(
                    f"Missing required tables: {', '.join(missing_tables)}. "
                    "Please run './pkm.sh init-db' to initialize the database."
                )
                
            conn.close()
        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}. Please run './pkm.sh init-db' to initialize the database.")

    def create_daily_log(self, date=None):
        """
        Create a new daily log from template.
        
        Args:
            date (str, optional): Date in YYYY-MM-DD format. Defaults to today.
            
        Note:
            - Creates file in daily_dir using daily_template.md
            - Replaces {{date}} placeholder in template
            - Skips creation if file already exists
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        template_path = os.path.join(self.templates_dir, 'daily_template.md')
        daily_path = os.path.join(self.daily_dir, f'{date}.md')
        
        if os.path.exists(daily_path):
            print(f"Daily log for {date} already exists!")
            return
            
        with open(template_path, 'r') as template:
            content = template.read()
            
        # Replace template variables
        content = content.replace('{{date}}', date)
        
        with open(daily_path, 'w') as daily_file:
            daily_file.write(content)
            
        print(f"Created daily log for {date}")

    def get_daily_journal(self):
        """
        Get today's journal content or create new if not exists.
        
        Returns:
            str: Content of today's journal file
            
        Note:
            Automatically creates new journal if none exists for today
        """
        date = datetime.now().strftime('%Y-%m-%d')
        daily_path = os.path.join(self.daily_dir, f'{date}.md')
        
        if not os.path.exists(daily_path):
            self.create_daily_log(date)
        
        with open(daily_path, 'r') as f:
            return f.read()

    def get_metrics(self):
        """
        Get recent daily metrics.
        
        Returns:
            str: Formatted string of recent metrics (last 7 days)
            
        Metrics Include:
            - Date
            - Mood rating (0-10)
            - Energy level (0-10)
            - Sleep hours
            - Optional notes
        """
        self.check_database()
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, mood_rating, energy_level, sleep_hours, notes
            FROM daily_metrics
            ORDER BY date DESC
            LIMIT 7
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No metrics recorded yet."
        
        result = "Recent Daily Metrics:\n\n"
        for row in rows:
            result += f"Date: {row[0]}\n"
            result += f"Mood: {row[1]}/10\n"
            result += f"Energy: {row[2]}/10\n"
            result += f"Sleep: {row[3]} hours\n"
            if row[4]:
                result += f"Notes: {row[4]}\n"
            result += "-" * 30 + "\n"
        
        return result

    def get_work_log(self):
        """
        Get recent work logs.
        
        Returns:
            str: Formatted string of recent work logs (last 10 entries)
            
        Log Details:
            - Date
            - Project name (if specified)
            - Hours worked
            - Work description (if provided)
        """
        self.check_database()
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, project, total_hours, description
            FROM work_logs
            ORDER BY date DESC
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No work hours logged yet."
        
        result = "Recent Work Logs:\n\n"
        for row in rows:
            result += f"Date: {row[0]}\n"
            if row[1]:
                result += f"Project: {row[1]}\n"
            result += f"Hours: {row[2]:.2f}\n"
            if row[3]:
                result += f"Description: {row[3]}\n"
            result += "-" * 30 + "\n"
        
        return result

    def get_habits(self):
        """
        Get habits and recent completions.
        
        Returns:
            str: Formatted string of habits and their completion stats
            
        Stats Include:
            - Habit name
            - Total times completed
            - Date of last completion
        """
        self.check_database()
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.name,
                   COUNT(hl.id) as completions,
                   MAX(hl.completed_at) as last_completed
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id
            GROUP BY h.id
            ORDER BY h.name
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No habits tracked yet."
        
        result = "Habit Tracking:\n\n"
        for row in rows:
            result += f"Habit: {row[0]}\n"
            result += f"Total Completions: {row[1]}\n"
            if row[2]:
                result += f"Last Completed: {row[2]}\n"
            result += "-" * 30 + "\n"
        
        return result

    def get_alcohol_log(self):
        """
        Get recent alcohol logs.
        
        Returns:
            str: Formatted string of recent alcohol consumption (last 10 entries)
            
        Log Details:
            - Date
            - Type of drink
            - Units consumed
            - Optional notes
        """
        self.check_database()
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, drink_type, units, notes
            FROM alcohol_logs
            ORDER BY date DESC
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No alcohol consumption logged yet."
        
        result = "Recent Alcohol Logs:\n\n"
        for row in rows:
            result += f"Date: {row[0]}\n"
            result += f"Drink: {row[1]}\n"
            result += f"Units: {row[2]}\n"
            if row[3]:
                result += f"Notes: {row[3]}\n"
            result += "-" * 30 + "\n"
        
        return result

    def get_recent_logs(self):
        """
        Get recent daily logs.
        
        Returns:
            str: Formatted string of recent daily logs (last 5 entries)
            
        Note:
            Returns full content of each log file
        """
        logs = []
        for filename in sorted(os.listdir(self.daily_dir), reverse=True)[:5]:
            if filename.endswith('.md'):
                with open(os.path.join(self.daily_dir, filename), 'r') as f:
                    logs.append((filename[:-3], f.read()))
        
        if not logs:
            return "No daily logs found."
        
        result = "Recent Daily Logs:\n\n"
        for date, content in logs:
            result += f"=== {date} ===\n"
            result += content + "\n"
            result += "=" * 50 + "\n\n"
        
        return result

    def query_database(self):
        """
        Get a summary of database statistics.
        
        Returns:
            str: Formatted string of database statistics
            
        Statistics Include:
            - Daily metrics summary (counts and averages)
            - Total habits completed
            - Work log summary (entries and total hours)
            - Alcohol log summary (entries and total units)
        """
        self.check_database()
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        stats = []
        
        # Get metrics stats
        cursor.execute('SELECT COUNT(*), AVG(mood_rating), AVG(energy_level), AVG(sleep_hours) FROM daily_metrics')
        row = cursor.fetchone()
        if row[0] > 0:
            stats.append(f"Daily Metrics Entries: {row[0]}")
            stats.append(f"Average Mood: {row[1]:.1f}/10")
            stats.append(f"Average Energy: {row[2]:.1f}/10")
            stats.append(f"Average Sleep: {row[3]:.1f} hours")
        
        # Get habit stats
        cursor.execute('SELECT COUNT(*) FROM habit_logs')
        habits_completed = cursor.fetchone()[0]
        stats.append(f"Total Habits Completed: {habits_completed}")
        
        # Get work stats
        cursor.execute('SELECT COUNT(*), SUM(total_hours) FROM work_logs')
        row = cursor.fetchone()
        if row[0] > 0:
            stats.append(f"Work Log Entries: {row[0]}")
            stats.append(f"Total Hours Worked: {row[1]:.1f}")
        
        # Get alcohol stats
        cursor.execute('SELECT COUNT(*), SUM(units) FROM alcohol_logs')
        row = cursor.fetchone()
        if row[0] > 0:
            stats.append(f"Alcohol Log Entries: {row[0]}")
            stats.append(f"Total Units Consumed: {row[1]:.1f}")
        
        conn.close()
        
        if not stats:
            return "No data recorded yet."
        
        return "Database Statistics:\n\n" + "\n".join(stats)

    def log_habit(self, habit_name, completed=True, notes=None):
        """
        Log a habit completion.
        
        Args:
            habit_name (str): Name of the habit
            completed (bool, optional): Whether habit was completed. Defaults to True.
            notes (str, optional): Additional notes about completion
            
        Note:
            Creates habit if it doesn't exist
        """
        self.check_database()  # Check database before operation
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get or create habit
        cursor.execute('''
            INSERT OR IGNORE INTO habits (name, frequency)
            VALUES (?, 'daily')
        ''', (habit_name,))
        
        cursor.execute('SELECT id FROM habits WHERE name = ?', (habit_name,))
        habit_id = cursor.fetchone()[0]
        
        # Log completion
        cursor.execute('''
            INSERT INTO habit_logs (habit_id, notes)
            VALUES (?, ?)
        ''', (habit_id, notes))
        
        conn.commit()
        conn.close()
        
        print(f"Logged habit: {habit_name}")

    def log_alcohol(self, drink_type, units, notes=None):
        """
        Log alcohol consumption.
        
        Args:
            drink_type (str): Type of alcoholic drink
            units (float): Number of alcohol units
            notes (str, optional): Additional notes about consumption
        """
        self.check_database()  # Check database before operation
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alcohol_logs (date, drink_type, units, notes)
            VALUES (date('now'), ?, ?, ?)
        ''', (drink_type, units, notes))
        
        conn.commit()
        conn.close()
        
        print(f"Logged {units} units of {drink_type}")

    def log_work_hours(self, start_time, end_time=None, project=None, description=None):
        """
        Log work hours using start and end time.
        
        Args:
            start_time (str): Start time in YYYY-MM-DD HH:MM:SS format
            end_time (str, optional): End time in YYYY-MM-DD HH:MM:SS format. Defaults to now.
            project (str, optional): Project name
            description (str, optional): Work description
            
        Note:
            Automatically calculates total hours from time difference
        """
        self.check_database()  # Check database before operation
        if end_time is None:
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        total_hours = (end - start).total_seconds() / 3600
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO work_logs (date, start_time, end_time, project, description, total_hours)
            VALUES (date(?), ?, ?, ?, ?, ?)
        ''', (start_time, start_time, end_time, project, description, total_hours))
        
        conn.commit()
        conn.close()
        
        print(f"Logged {total_hours:.2f} hours of work")

    def log_work_hours_direct(self, hours, project=None, description=None):
        """
        Log work hours directly without start/end time.
        
        Args:
            hours (float): Number of hours worked
            project (str, optional): Project name
            description (str, optional): Work description
            
        Note:
            Uses current timestamp for both start and end time
        """
        self.check_database()  # Check database before operation
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO work_logs (date, start_time, end_time, project, description, total_hours)
            VALUES (date(?), ?, ?, ?, ?, ?)
        ''', (now, now, now, project, description, hours))
        
        conn.commit()
        conn.close()
        
        print(f"Logged {hours:.2f} hours of work")

    def log_daily_metrics(self, mood, energy, sleep_hours, notes=None):
        """
        Log daily metrics.
        
        Args:
            mood (int): Mood rating (0-10)
            energy (int): Energy level (0-10)
            sleep_hours (float): Hours of sleep
            notes (str, optional): Additional notes about the day
            
        Note:
            Replaces existing metrics for current date if any exist
        """
        self.check_database()  # Check database before operation
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_metrics 
            (date, mood_rating, energy_level, sleep_hours, notes)
            VALUES (date('now'), ?, ?, ?, ?)
        ''', (mood, energy, sleep_hours, notes))
        
        conn.commit()
        conn.close()
        
        print("Logged daily metrics")
