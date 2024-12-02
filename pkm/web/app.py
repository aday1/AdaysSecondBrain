# Existing imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
import os
import json
import sqlite3  # Add this line to import sqlite3
from datetime import datetime, timedelta
import sys
import argparse
import markdown
import logging
from time import strftime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # Added import for text

conn = sqlite3.connect('pkm/db/pkm.db', timeout=10)  # Timeout in seconds

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pkm_manager import PKMManager
from utils import format_timestamp

# Configure logging before creating the app
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.debug = True  # Enable debug mode

# Configure Werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)

# Configure the Flask app to use SQLAlchemy
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'pkm.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 5
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800

# Ensure the database directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SQLAlchemy(app)

# Add request logging
@app.before_request
def before_request():
    app.logger.debug(f'\nRequest: {request.method} {request.url}')
    app.logger.debug(f'Headers: {dict(request.headers)}')
    app.logger.debug(f'Body: {request.get_data().decode()}')

@app.after_request
def after_request(response):
    app.logger.debug(f'Response Status: {response.status}')
    app.logger.debug(f'Response Headers: {dict(response.headers)}')
    return response

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class PKMManager:
    def __init__(self):
        self.db_path = db_path
        self.daily_dir = os.path.join(os.path.dirname(__file__), 'daily_logs')  # Ensure this line is present
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')  # Add this line

    def get_db_connection(self):
        return db.engine.raw_connection()  # Changed to return raw DBAPI connection

pkm = PKMManager()

app.logger.info(f"Database path: {pkm.db_path}")  # Debug output
app.logger.info(f"Database exists: {os.path.exists(pkm.db_path)}")  # Debug output

# Initialize database with core tables
def get_day_period():
    """Helper function to determine period of day"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 21:
        return 'evening'
    else:
        return 'night'

# ...existing code...
def init_db():
    app.logger.info("Checking database tables...")
    
    os.makedirs('db', exist_ok=True)
    
    with app.app_context():
        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        try:
            # Check if tables exist first
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Only initialize if key tables are missing
            required_tables = {'daily_metrics', 'work_logs', 'projects', 'habits'}
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                app.logger.info(f"Missing tables detected: {missing_tables}")
                init_sql_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'init.sql')
                app.logger.info(f"Loading SQL from: {init_sql_path}")

                with open(init_sql_path, 'r') as f:
                    sql_script = f.read()
                    
                    # Clean up SQL script
                    lines = []
                    for line in sql_script.splitlines():
                        clean_line = line.split('--')[0].strip()
                        if clean_line:
                            lines.append(clean_line)
                    cleaned_sql = '\n'.join(lines)
                    cleaned_sql = cleaned_sql.replace(';;', ';')
                    
                    cursor.executescript(cleaned_sql)
                    conn.commit()
                    app.logger.info("Database tables created successfully")
            else:
                app.logger.info("All required tables exist")

        except Exception as e:
            app.logger.error(f"Error checking/initializing database: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

# ...existing code...

# Call init_db when the app starts (will only create tables if they don't exist)
init_db()

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'web_enabled': False, 'username': 'admin', 'password_hash': None}
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding JSON from config file: {config_path}")
        return {'web_enabled': False, 'username': 'admin', 'password_hash': None}

# Initialize app configuration from config.json
config = load_config()
app.secret_key = config.get('secret_key', os.urandom(24))

# Make config and global functions available to all templates
@app.context_processor
def inject_config():
    return dict(
        site_title=config.get('title', 'Personal Knowledge Management'),
        min=min  # Add min() function to templates
    )

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.template_filter('format_date')
def format_date_filter(date):
    """Convert date to format with month name"""
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    return date.strftime('%B %d, %Y')  # e.g., "January 01, 2024"

def get_mood_emoji(value):
    """Helper function to get mood emoji based on value (1-100)"""
    if value <= 20:
        return '😫'
    elif value <= 40:
        return '😐'
    elif value <= 60:
        return '🙂'
    elif value <= 80:
        return '😊'
    else:
        return '😄'

def get_energy_emoji(value):
    """Helper function to get energy emoji based on value (1-100)"""
    if value <= 33:
        return '🔋'
    elif value <= 66:
        return '⚡'
    else:
        return '⚡����'

# Add after the other template filters
@app.template_filter('sum')
def sum_filter(iterable, attribute=None):
    """Custom sum filter that handles None values and ensures float conversion"""
    if attribute:
        values = [getattr(x, attribute, 0) or 0 for x in iterable]
    else:
        values = [x or 0 for x in iterable]
    return sum(float(v) for v in values)

# ...existing code...

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        config = load_config()
        if not config['web_enabled']:
            flash('Web interface is disabled')
            return redirect(url_for('login'))
            
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == config['username'] and check_password_hash(config['password_hash'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))  # Updated redirect to dashboard
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view showing overview of various metrics"""
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    date_range = request.args.get('range', 'day')
    
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    try:
        stats = {
            'mood': 0,
            'energy': 0,
            'sleep_hours': 0,
            'work_hours': 0,
            'habits_completed': 0,
            'total_habits': 0
        }

        # Adjust query based on date range
        date_filters = {
            'day': "date = ?",
            'week': "date >= date(?, '-6 days') AND date <= ?",
            'month': "date >= date(?, 'start of month') AND date <= date(?, 'end of month')",
            'year': "date >= date(?, 'start of year') AND date <= date(?, 'end of year')"
        }
        
        date_filter = date_filters.get(date_range, date_filters['day'])
        
        # Update queries to use date range
        cursor.execute(f'''
            SELECT AVG(mood_level), AVG(energy_level)
            FROM sub_mood_logs  
            WHERE {date_filter}
        ''', (selected_date, selected_date) if date_range != 'day' else (selected_date,))
        
        # ...rest of existing queries with similar date range handling...
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             selected_date=selected_date,
                             date_range=date_range)
        
    except Exception as e:
        app.logger.error(f'Error loading dashboard: {str(e)}')
        flash('Error loading dashboard data')
        return render_template('dashboard.html', 
                             stats=stats, 
                             selected_date=selected_date,
                             date_range=date_range)
    finally:
        cursor.close()
        conn.close()

# ...existing code...

@app.route('/daily_logs', methods=['GET', 'POST'])
@login_required
def daily_logs():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    logs = []
    work_hours = 0
    habit_completion_count = 0

    if request.method == 'POST':
        # ...existing code...
        today = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(pkm.daily_dir, f'{today}.md')

        # Ensure the daily logs directory exists
        os.makedirs(pkm.daily_dir, exist_ok=True)

        # ...existing code...
        if not os.path.exists(file_path):
            # ...existing code...
            template_path = os.path.join(pkm.templates_dir, 'daily_template.md')
            try:
                with open(template_path, 'r') as f:
                    template_content = f.read()
                # ...existing code...
                content = template_content.replace('{{date}}', today)
            except FileNotFoundError:
                content = f"# Daily Log - {today}\n\n## Notes\n\n## Tasks\n\n## Reflections\n"

            # ...existing code...
            with open(file_path, 'w') as f:
                f.write(content)
            flash('Created new daily log')
        else:
            flash('Daily log already exists')

        return redirect(url_for('daily_logs', date=today))

    # ...existing code...
    try:
        conn = pkm.get_db_connection()
        cursor = conn.connection.cursor()  # Use the correct method to get a cursor

        # ...existing code...
        if os.path.exists(pkm.daily_dir):
            for log_file in sorted(os.listdir(pkm.daily_dir), reverse=True):
                if log_file.endswith('.md'):
                    with open(os.path.join(pkm.daily_dir, log_file), 'r') as f:
                        content = f.read()
                        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                        logs.append({
                            'date': log_file.replace('.md', ''),
                            'content': html_content,
                            'raw_content': content
                        })

        # ...existing code...
        cursor.execute('''
            SELECT SUM(total_hours)
            FROM work_logs
            WHERE date = ?
        ''', (selected_date,))
        work_hours_data = cursor.fetchone()
        work_hours = work_hours_data[0] if work_hours_data and work_hours_data[0] is not None else 0

        # ...existing code...
        cursor.execute('''
            SELECT COUNT(*)
            FROM habit_logs
            WHERE completed_at >= datetime(?, 'start of day')
            AND completed_at < datetime(?, 'start of day', '+1 day')
        ''', (selected_date, selected_date))
        habit_completion_data = cursor.fetchone()
        habit_completion_count = habit_completion_data[0] if habit_completion_data else 0

    except Exception as e:
        flash(f'Error reading logs: {str(e)}')
        app.logger.error(f'Error reading logs: {str(e)}')

    # ...existing code...
    previous_date = (datetime.strptime(selected_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (datetime.strptime(selected_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

    # Ensure the daily logs directory exists
    os.makedirs(pkm.daily_dir, exist_ok=True)

    # ...existing code...
    file_path = os.path.join(pkm.daily_dir, f'{selected_date}.md')
    if not os.path.exists(file_path):
        # ...existing code...
        template_path = os.path.join(pkm.templates_dir, 'daily_template.md')
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            # ...existing code...
            content = template_content.replace('{{date}}', selected_date)
        except FileNotFoundError:
            content = f"# Daily Log - {selected_date}\n\n## Notes\n\n## Tasks\n\n## Reflections\n"

        # ...existing code...
        with open(file_path, 'w') as f:
            f.write(content)
        flash('Created new daily log for the selected date')

    return render_template('daily_logs.html', logs=logs, selected_date=selected_date,
                           work_hours=work_hours, habit_completion_count=habit_completion_count,
                           previous_date=previous_date, next_date=next_date)

@app.route('/update_log/<date>', methods=['POST'])
@login_required
def update_log(date):
    content = request.form.get('content')
    file_path = os.path.join(pkm.daily_dir, f'{date}.md')
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        flash('Log updated successfully')
    except Exception as e:
        flash(f'Error updating log: {str(e)}')
        app.logger.error(f'Error reading logs: {str(e)}')
    
    return redirect(url_for('daily_logs', date=date))

@app.route('/save_gratitude', methods=['POST'])
@login_required
def save_gratitude():
    gratitude_content = request.form.get('gratitude_content')
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            INSERT INTO gratitude (content, date) VALUES (?, ?)
        ''', (gratitude_content, today))
        
        conn.commit()
        flash('Gratitude entry saved successfully')
    except Exception as e:
        flash(f'Error saving gratitude entry: {str(e)}')
    
    return redirect(url_for('gratitude'))  # Redirect to the gratitude page

@app.route('/gratitude', methods=['GET'])
@login_required
def gratitude():
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    # ...existing code...
    cursor.execute('''
        SELECT content, date, id FROM gratitude
        ORDER BY date DESC
    ''')
    gratitude_logs = cursor.fetchall()
    
    # ...existing code...
    conn.close()
    
    # ...existing code...
    return render_template('gratitude.html', gratitude_logs=gratitude_logs)

@app.route('/edit_gratitude/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_gratitude(id):
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    try:
        if request.method == 'POST':
            updated_content = request.form.get('gratitude_content')
            cursor.execute('''
                UPDATE gratitude SET content = ? WHERE id = ?
            ''', (updated_content, id))
            conn.commit()
            flash('Gratitude entry updated successfully')
            return redirect(url_for('gratitude'))

        # ...existing code...
        cursor.execute('SELECT content FROM gratitude WHERE id = ?', (id,))
        entry = cursor.fetchone()
        
        if entry:
            return render_template('edit_log.html', content=entry[0], id=id, log_type='gratitude')
        else:
            flash('Gratitude entry not found')
            return redirect(url_for('gratitude'))
            
    except Exception as e:
        flash(f'Error updating gratitude entry: {str(e)}')
        return redirect(url_for('gratitude'))
        
    finally:
        conn.close()

@app.route('/delete_gratitude/<int:id>', methods=['POST'])
@login_required
def delete_gratitude(id):
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM gratitude WHERE id = ?', (id,))
        conn.commit()
        flash('Gratitude entry deleted successfully')
    except Exception as e:
        flash(f'Error deleting gratitude entry: {str(e)}')
    
    return redirect(url_for('gratitude'))

@app.route('/get_mood_data', methods=['GET'])
@login_required
def get_mood_data():
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            SELECT timestamp, mood_level, energy_level, activity, notes
            FROM sub_mood_logs
            WHERE date = ?
            ORDER BY timestamp ASC
        ''', (date,))
        
        mood_data = cursor.fetchall()
        conn.close()
        
        data = {
            'labels': [row[0].split(' ')[1] for row in mood_data],  # Get time part only
            'mood_values': [row[1] for row in mood_data],
            'energy_values': [row[2] for row in mood_data],
            'activities': [row[3] for row in mood_data],
            'notes': [row[4] for row in mood_data]
        }
        
        return jsonify(data)
    except Exception as e:
        app.logger.error(f'Error in get_mood_data: {str(e)}')  # Log the error
        return jsonify({'error': str(e)}), 500

@app.route('/sleep_tracking', methods=['GET'])
@login_required
def sleep_tracking():
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, sleep_hours, sleep_quality, bedtime, wake_time, sleep_notes
            FROM daily_metrics
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
        ''')
        
        sleep_data = cursor.fetchall()
        conn.close()
        
        formatted_data = {
            'dates': [row[0] for row in sleep_data],
            'hours': [row[1] for row in sleep_data],
            'quality': [row[2] for row in sleep_data],
            'bedtimes': [row[3] for row in sleep_data],
            'wake_times': [row[4] for row in sleep_data],
            'notes': [row[5] for row in sleep_data]
        }
        
        return render_template('sleep_tracking.html', sleep_data=formatted_data)
        
    except Exception as e:
        app.logger.error(f'Error fetching sleep data: {str(e)}')
        return render_template('sleep_tracking.html', error=str(e), sleep_data={'dates': [], 'hours': [], 'quality': [], 'bedtimes': [], 'wake_times': [], 'notes': []})

# ...existing code...

@app.route('/get_sleep_data', methods=['GET'])
@login_required
def get_sleep_data():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            SELECT date, sleep_hours, sleep_quality, bedtime, wake_time, sleep_notes
            FROM daily_metrics
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
        ''')
        
        sleep_data = cursor.fetchall()
        conn.close()
        
        formatted_data = {
            'dates': [row[0] for row in sleep_data],
            'hours': [row[1] for row in sleep_data],
            'quality': [row[2] for row in sleep_data],
            'bedtimes': [row[3] for row in sleep_data],
            'wake_times': [row[4] for row in sleep_data],
            'notes': [row[5] for row in sleep_data]
        }
        
        return jsonify(formatted_data)
        
    except Exception as e:
        app.logger.error(f'Error fetching sleep data: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ...existing code...

@app.route('/get_sleep_metrics')
@login_required
def get_sleep_metrics():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                date,
                COALESCE(sleep_hours, 0) as sleep_hours,
                COALESCE(sleep_quality, 0) as sleep_quality,
                bedtime,
                wake_time,
                sleep_notes
            FROM daily_metrics
            WHERE date >= date('now', '-30 days')
            ORDER BY date ASC
        ''')
        
        metrics = cursor.fetchall()
        
        data = {
            'dates': [],
            'hours': [],
            'quality': [],
            'bedtimes': [],
            'wake_times': [],
            'notes': []
        }

        # ...existing code...
        if metrics:
            data = {
                'dates': [str(row[0]) for row in metrics],
                'hours': [float(row[1]) if row[1] is not None else 0 for row in metrics],
                'quality': [int(row[2]) if row[2] is not None else 0 for row in metrics],
                'bedtimes': [str(row[3]) if row[3] else '' for row in metrics],
                'wake_times': [str(row[4]) if row[4] else '' for row in metrics],
                'notes': [str(row[5]) if row[5] else '' for row in metrics]
            }
        
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Error getting sleep metrics: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# ...existing code...
@app.route('/log_sleep', methods=['POST'])
@login_required
def log_sleep():
    try:
        bedtime = request.form.get('bed_time')
        wake_time = request.form.get('wake_up_time')
        sleep_quality = int(request.form.get('sleep_quality', 0))
        sleep_notes = request.form.get('sleep_notes', '')

        if not all([bedtime, wake_time]):
            flash('Bedtime and wake time are required.')
            return redirect(url_for('sleep_tracking'))
        
        bed_dt = datetime.strptime(f"2000-01-01 {bedtime}", "%Y-%m-%d %H:%M")
        wake_dt = datetime.strptime(f"2000-01-01 {wake_time}", "%Y-%m-%d %H:%M")
        
        if wake_dt < bed_dt:
            flash('Wake time cannot be earlier than bedtime.')
            return redirect(url_for('sleep_tracking'))
        
        sleep_hours = (wake_dt - bed_dt).total_seconds() / 3600

        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO daily_metrics (
                date, sleep_hours, sleep_quality, bedtime, wake_time, sleep_notes
            ) VALUES (
                date('now'), ?, ?, ?, ?, ?
            )
        ''', (sleep_hours, sleep_quality, bedtime, wake_time, sleep_notes))
        
        conn.commit()
        
        # Redirect to sleep_tracking after successful insertion
        return redirect(url_for('sleep_tracking'))
    
    except Exception as e:
        app.logger.error(f'Error logging sleep data: {str(e)}')
        flash('Error logging sleep data.')
        return redirect(url_for('sleep_tracking'))
    
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

# ...existing code...

@app.route('/get_habits_data', methods=['GET'])
@login_required
def get_habits_data():
    try:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            SELECT 
                h.name,
                GROUP_CONCAT(DISTINCT date(hl.completed_at)) as completion_dates,
                h.frequency,
                h.streak
            FROM habits h
            LEFT JOIN habit_logs hl ON h.name = hl.habit_id
                AND date(hl.completed_at) >= date(?, '-6 days')
            GROUP BY h.name
        ''', (today,))
        
        habits_data = cursor.fetchall()
        
        # ...existing code...
        dates = [(today - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(6, -1, -1)]
        
        # ...existing code...
        chart_data = {
            'dates': dates,
            'datasets': []
        }
        
        for habit in habits_data:
            name, completion_dates, frequency, streak = habit
            completion_dates = completion_dates.split(',') if completion_dates else []
            
            # ...existing code...
            completions = []
            for date in dates:
                completions.append(1 if date in completion_dates else 0)
            
            chart_data['datasets'].append({
                'label': name,
                'data': completions,
                'frequency': frequency,
                'streak': streak
            })
        
        return jsonify(chart_data)
        
    except Exception as e:
        app.logger.error(f'Error in get_habits_data: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/habits')
@login_required
def habits():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    try:
        # Get all habits first for dropdown
        cursor.execute('SELECT name FROM habits ORDER BY name')
        all_habits = [{"name": row[0]} for row in cursor.fetchall()]
        
        # Get completed habits for today
        cursor.execute('''
            SELECT DISTINCT habit_id 
            FROM habit_logs 
            WHERE date(completed_at) = date('now')
        ''')
        completed_habits = [row[0] for row in cursor.fetchall()]
        
        # Get detailed habit statistics with proper rates
        cursor.execute('''
            SELECT 
                h.name,
                h.frequency,
                h.description,
                h.streak,
                COALESCE((SELECT COUNT(*) FROM habit_logs 
                         WHERE habit_id = h.name 
                         AND date(completed_at) = date('now')), 0) as today_count,
                COALESCE((SELECT COUNT(DISTINCT date(completed_at)) FROM habit_logs 
                         WHERE habit_id = h.name 
                         AND date(completed_at) >= ?), 0) as week_count,
                COALESCE((SELECT COUNT(DISTINCT date(completed_at)) FROM habit_logs 
                         WHERE habit_id = h.name 
                         AND date(completed_at) >= ?), 0) as month_count,
                (SELECT MAX(completed_at) FROM habit_logs 
                 WHERE habit_id = h.name) as last_completed
            FROM habits h
        ''', (week_start, month_start))
        
        habits_data = cursor.fetchall()
        
        # Process habits data
        processed_habits = []
        for habit in habits_data:
            name, frequency, description, streak, today_count, week_count, month_count, last_completed = habit
            
            # Calculate completion rates based on frequency
            week_target = {
                'daily': 7,
                'weekly': 1,
                'monthly': 0.25
            }.get(frequency, 7)
            
            month_target = {
                'daily': 30,
                'weekly': 4,
                'monthly': 1
            }.get(frequency, 30)
            
            # Calculate rates with safe division
            week_rate = min(int((week_count / week_target * 100) if week_target else 0), 100)
            month_rate = min(int((month_count / month_target * 100) if month_target else 0), 100)
            
            # Check streak
            if last_completed:
                last_completed = datetime.strptime(last_completed, '%Y-%m-%d %H:%M:%S').date()
                days_since_last = (today - last_completed).days
                
                if (frequency == 'daily' and days_since_last > 1) or \
                   (frequency == 'weekly' and days_since_last > 7) or \
                   (frequency == 'monthly' and days_since_last > 30):
                    streak = 0
            
            processed_habits.append({
                'name': name,
                'frequency': frequency,
                'description': description,
                'streak': streak,
                'today_complete': today_count > 0,
                'week_rate': week_rate,
                'month_rate': month_rate,
                'last_completed': last_completed
            })
        
        return render_template('habits.html', 
                             habits=all_habits,
                             processed_habits_data=processed_habits,
                             completed_habits=completed_habits)
                             
    except Exception as e:
        app.logger.error(f'Error in habits route: {str(e)}')
        flash(f'Error loading habits: {str(e)}')
        return render_template('habits.html', 
                             habits=[],
                             processed_habits_data=[],
                             completed_habits=[])
    finally:
        cursor.close()
        conn.close()

# ...existing code...

@app.route('/mark_complete/<habit_name>', methods=['POST'])
@login_required
def mark_complete(habit_name):
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        completed = request.form.get('completed') == 'on'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if completed:
            # ...existing code...
            cursor.execute('''
                INSERT INTO habit_logs (habit_id, completed_at)
                VALUES (?, ?)
            ''', (habit_name, now))
            
            # ...existing code...
            cursor.execute('''
                UPDATE habits 
                SET streak = streak + 1
                WHERE name = ?
            ''', (habit_name,))
            
            flash(f'Marked {habit_name} as completed')
        else:
            # ...existing code...
            cursor.execute('''
                DELETE FROM habit_logs 
                WHERE habit_id = ? 
                AND date(completed_at) = date('now')
            ''', (habit_name,))
            
            # ...existing code...
            cursor.execute('''
                UPDATE habits 
                SET streak = 0
                WHERE name = ?
            ''', (habit_name,))
            
            flash(f'Unmarked {habit_name} as completed')
        
        conn.commit()
        
    except Exception as e:
        flash(f'Error updating habit: {str(e)}')
        app.logger.error(f'Error in mark_complete: {str(e)}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('habits'))

@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    try:
        existing_habit = request.form.get('existing_habit')
        new_habit_name = request.form.get('habit')
        frequency = request.form.get('frequency')
        notes = request.form.get('notes')

        # ...existing code...
        habit_name = new_habit_name if existing_habit == 'new' else existing_habit
        
        if not habit_name or not habit_name.strip():
            flash('Habit name is required')
            return redirect(url_for('habits'))

        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        try:
            # ...existing code...
            cursor.execute('SELECT name FROM habits WHERE name = ?', (habit_name,))
            if cursor.fetchone() and existing_habit == 'new':
                flash('A habit with this name already exists')
                return redirect(url_for('habits'))

            # ...existing code...
            cursor.execute('''
                INSERT OR IGNORE INTO habits (name, frequency, description)
                VALUES (?, ?, ?)
            ''', (habit_name, frequency, notes))
            
            conn.commit()
            flash('Habit added successfully')
            
        except sqlite3.IntegrityError:
            flash('Error: Habit already exists')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('habits'))

    except Exception as e:
        app.logger.error(f'Error adding habit: {str(e)}')
        flash(f'Error adding habit: {str(e)}')
        return redirect(url_for('habits'))

@app.route('/debug_sleep_data', methods=['GET'])
@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form.get('title')
        notes = request.form.get('notes')
        completion = request.form.get('completion', 0)
        
        try:
            cursor.execute('''
                INSERT INTO goals (title, notes, completion, status)
                VALUES (?, ?, ?, 'active')
            ''', (title, notes, completion))
            conn.commit()
            flash('Goal added successfully')
        except Exception as e:
            flash(f'Error adding goal: {str(e)}')
    
    # ...existing code...
    cursor.execute('''
        SELECT id, title, notes, completion, status 
        FROM goals 
        WHERE status = 'active' 
        ORDER BY created_at DESC
    ''')
    goals = [dict(zip(['id', 'title', 'notes', 'completion', 'status'], row)) for row in cursor.fetchall()]
    
    conn.close()
    return render_template('goals.html', goals=goals)

@app.route('/update_goal_completion/<goal_name>', methods=['POST'])
@login_required
def update_goal_completion(goal_name):
    data = request.get_json()
    completion = data.get('completion')
    
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    status = 'completed' if int(completion) >= 100 else 'active'
    completed_at = datetime.now() if status == 'completed' else None
    
    # ...existing code...
    cursor.execute('SELECT id FROM goals WHERE title = ?', (goal_name,))
    goal_id = cursor.fetchone()[0]
    
    # ...existing code...
    cursor.execute('''
        UPDATE goals 
        SET completion = ?,
            status = ?,
            completed_at = ?
        WHERE title = ?
    ''', (completion, status, completed_at, goal_name))
    
    # ...existing code...
    cursor.execute('''
        INSERT INTO goal_progress_history (goal_id, completion)
        VALUES (?, ?)
    ''', (goal_id, completion))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': status})

@app.route('/get_goal_progress/<int:goal_id>')
@login_required
def get_goal_progress(goal_id):
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT completion, timestamp 
        FROM goal_progress_history 
        WHERE goal_id = ? 
        ORDER BY timestamp ASC
    ''', (goal_id,))
    
    history = cursor.fetchall()
    conn.close()
    
    dates = [h[1].split(' ')[0] for h in history]  # Get just the date part
    progress = [h[0] for h in history]
    
    return jsonify({
        'dates': dates,
        'progress': progress
    })

@app.route('/update_goal_notes/<goal_name>', methods=['POST'])
@login_required
def update_goal_notes(goal_name):
    data = request.get_json()
    notes = data.get('notes')
    
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE goals 
        SET notes = ?
        WHERE title = ?
    ''', (notes, goal_name))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/mark_goal_complete/<goal_name>', methods=['POST'])
@login_required
def mark_goal_complete(goal_name):
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            UPDATE goals 
            SET status = 'completed' 
            WHERE title = ?
        ''', (goal_name,))
        
        conn.commit()
        flash(f'Goal "{goal_name}" marked as complete.')
    except Exception as e:
        flash(f'Error marking goal as complete: {str(e)}')
    
    return redirect(url_for('goals'))

@app.route('/routines', methods=['GET', 'POST'])
@login_required
def routines():
    conn = pkm.get_db_connection()
    
    if request.method == 'POST':
        routine_name = request.form.get('routine_name')
        routine_time = request.form.get('routine_time')
        routine_frequency = request.form.get('routine_frequency')
        routine_day = request.form.get('routine_day')
        
        if not routine_frequency:
            flash('Routine frequency is required')
            return redirect(url_for('routines'))
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO routines (name, routine_time, frequency, day)
                VALUES (?, ?, ?, ?)
            ''', (routine_name, routine_time, routine_frequency, routine_day))
            conn.commit()
            flash('Routine added successfully')
        except Exception as e:
            flash(f'Error adding routine: {str(e)}')
        finally:
            cursor.close()
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, routine_time, frequency, day, status 
            FROM routines 
            WHERE status = 'active' OR status IS NULL
            ORDER BY routine_time ASC
        ''')
        routines = cursor.fetchall()
    except Exception as e:
        flash(f'Error fetching routines: {str(e)}')
        routines = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('routines.html', routines=routines)

@app.route('/mark_routine_complete/<routine_name>', methods=['POST'])
@login_required
def mark_routine_complete(routine_name):
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE routines 
            SET status = 'completed' 
            WHERE name = ? AND (status = 'active' OR status IS NULL)
        ''', (routine_name,))
        
        conn.commit()
        flash(f'Routine "{routine_name}" marked as complete.')
    except Exception as e:
        flash(f'Error marking routine as complete: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('routines'))

@app.route('/alcohol', methods=['GET', 'POST'])
@login_required
def alcohol():
    if request.method == 'POST':
        try:
            drink_type = request.form.get('drink_type')
            new_drink = request.form.get('new-drink')
            units = float(request.form.get('units', 0))
            notes = request.form.get('notes')

            # ...existing code...
            if drink_type == 'new':
                drink_type = new_drink.strip()
                if not drink_type:
                    flash('Please enter a new drink type')
                    return redirect(url_for('alcohol'))

            conn = db.engine.raw_connection()
            cursor = conn.cursor()

            # ...existing code...
            cursor.execute('''
                INSERT INTO alcohol_logs (date, drink_type, units, notes, logged_at)
                VALUES (date('now'), ?, ?, ?, datetime('now'))
            ''', (drink_type, units, notes))

            conn.commit()
            flash('Alcohol consumption logged successfully')
            return redirect(url_for('alcohol'))

        except Exception as e:
            flash(f'Error logging alcohol consumption: {str(e)}')
            return redirect(url_for('alcohol'))

    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    # ...existing code...
    cursor.execute('SELECT DISTINCT drink_type FROM alcohol_logs')
    drink_types = [row[0] for row in cursor.fetchall()]
    
    # ...existing code...
    cursor.execute('SELECT * FROM alcohol_logs ORDER BY logged_at DESC LIMIT 10')
    alcohol_logs = cursor.fetchall()

    # ...existing code...
    one_week_ago = datetime.now() - timedelta(days=7)
    cursor.execute('''
        SELECT SUM(units) FROM alcohol_logs WHERE logged_at >= ?
    ''', (one_week_ago,))
    weekly_total = cursor.fetchone()[0] or 0

    conn.close()
    
    return render_template('alcohol.html', drink_types=drink_types, alcohol_logs=alcohol_logs, weekly_total=weekly_total)

# ...existing code...
@app.route('/medications', methods=['GET', 'POST'])
@login_required
def medications():
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            dosage = request.form['dosage']
            frequency = request.form['frequency']
            time_of_day = request.form['time_of_day']
            notes = request.form.get('notes', '')
            refill_date = request.form.get('refill_date', '')  # Get refill date

            cursor.execute('''
                INSERT INTO medications (name, dosage, frequency, time_of_day, notes, refill_date, active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (name, dosage, frequency, time_of_day, notes, refill_date))
            conn.commit()
            flash('Medication added successfully!')
        except Exception as e:
            flash(f'Error adding medication: {str(e)}')
            
    # ...existing code...
    cursor.execute('''
        SELECT id, name, dosage, frequency, time_of_day, notes, refill_date, active
        FROM medications 
        WHERE active = 1
    ''')
    medications_data = cursor.fetchall()
    
    medications = [
        {
            'id': row[0],
            'name': row[1],
            'dosage': row[2],
            'frequency': row[3],
            'time_of_day': row[4],
            'notes': row[5],
            'refill_date': row[6]
        } for row in medications_data
    ]
    
    # ...existing code...
    cursor.execute('''
        SELECT ml.taken_at, m.name as medication_name, ml.notes, m.refill_date
        FROM medication_logs ml 
        JOIN medications m ON ml.medication_id = m.id 
        ORDER BY ml.taken_at DESC 
        LIMIT 10
    ''')
    medication_logs = cursor.fetchall()
    
    conn.close()
    return render_template('medications.html', medications=medications, medication_logs=medication_logs)

@app.route('/log_medication', methods=['POST'])
@login_required
def log_medication():
    medication_id = request.form.get('medication_id')
    if not medication_id:
        flash('No medication specified')
        return redirect(url_for('medications'))
        
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medication_logs (medication_id, taken_at) 
            VALUES (?, datetime('now'))
        ''', (medication_id,))
        conn.commit()
        flash('Medication logged successfully!')
    except Exception as e:
        flash(f'Error logging medication: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('medications'))

@app.route('/deactivate_medication', methods=['POST'])
@login_required
def deactivate_medication():
    medication_id = request.form.get('medication_id')
    if not medication_id:
        flash('No medication specified')
        return redirect(url_for('medications'))
        
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE medications 
            SET active = 0 
            WHERE id = ?
        ''', (medication_id,))
        conn.commit()
        flash('Medication removed successfully!')
    except Exception as e:
        flash(f'Error removing medication: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('medications'))

@app.route('/check_medication_reminders')
def check_medication_reminders():
    # ...existing code...
    now = datetime.now().strftime('%H:%M')
    
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # ...existing code...
        cursor.execute('SELECT * FROM medication_reminders WHERE reminder_time = ?', (now,))
        reminders = cursor.fetchall()
        
        if reminders:
            # ...existing code...
            reminder = {
                'id': reminders[0][0],
                'medication_id': reminders[0][1],
                'reminder_time': reminders[0][2]
            }
            return jsonify(reminder=True, medication=reminder)
            
        return jsonify(reminder=False)
        
    except Exception as e:
        app.logger.error(f'Error checking medication reminders: {str(e)}')
        return jsonify(error=str(e)), 500
        
    finally:
        conn.close()

# ...existing code...

@app.route('/delete_subscription/<int:id>', methods=['POST'])
@login_required
def delete_subscription(id):
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM finance_forecast WHERE id = ?', (id,))
        conn.commit()
        flash('Subscription deleted successfully', 'success')
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error deleting subscription: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('finance_forecast'))

# ...existing code...
@app.route('/anxiety_tracking', methods=['GET'])
@login_required
def anxiety_tracking():
    return render_template('anxiety_tracking.html')

@app.route('/save_anxiety_data', methods=['POST'])
@login_required
def save_anxiety_data():
    try:
        data = request.get_json()
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO anxiety_logs (
                date, time_started, duration_minutes, suds_score,
                social_isolation, insufficient_self_control,
                subjugation, negativity, unrelenting_standards,
                trigger_id, coping_strategy_id, effectiveness,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['date'],
            data['timeStarted'],  # Ensure time_started column exists
            data['durationMinutes'],
            data['sudsScore'],
            data['socialIsolation'],
            data['insufficientSelfControl'],
            data['subjugation'],
            data['negativity'],
            data['unrelentingStandards'],
            data.get('trigger'),
            data.get('copingStrategy'),
            data['effectiveness'],
            data.get('notes', '')
        ))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f'Error saving anxiety data: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_anxiety_data', methods=['GET'])
@login_required
def get_anxiety_data():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                a.date, 
                a.time_started, 
                a.suds_score, 
                a.social_isolation, 
                a.insufficient_self_control, 
                a.subjugation, 
                a.negativity,
                a.unrelenting_standards,
                a.effectiveness,
                t.name as trigger_name,
                cs.name as strategy_name,
                a.duration_minutes,
                a.notes
            FROM anxiety_logs a
            LEFT JOIN anxiety_triggers t ON a.trigger_id = t.id
            LEFT JOIN coping_strategies cs ON a.coping_strategy_id = cs.id
            ORDER BY a.date ASC, a.time_started ASC
        ''')
        
        logs = cursor.fetchall()
        data = {
            'timestamps': [],
            'suds': [],
            'social': [],
            'control': [],
            'subjugation': [],
            'negativity': [],
            'standards': [],
            'logs': []
        }
        
        for log in logs:
            timestamp = f"{log[0]}T{log[1]}"
            data['timestamps'].append(timestamp)
            data['suds'].append(log[2])
            data['social'].append(log[3])
            data['control'].append(log[4])
            data['subjugation'].append(log[5])
            data['negativity'].append(log[6])
            data['standards'].append(log[7])
            
            data['logs'].append({
                'timestamp': timestamp,
                'suds': log[2],
                'trigger': log[9] or 'No trigger specified',
                'strategy': log[10] or 'No strategy specified',
                'effectiveness': log[8],
                'duration': log[11],
                'notes': log[12] or ''
            })
        
        return jsonify(data)
    except Exception as e:
        app.logger.error(f'Error fetching anxiety data: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ...existing code...
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# ...existing code...
@app.route('/finance_forecast', methods=['GET', 'POST'])
@login_required
def finance_forecast():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        renewal_date = request.form.get('renewal_date')
        monthly_cost = float(request.form.get('monthly_cost'))
        category = request.form.get('category')
        yearly_total = monthly_cost * 12
        
        try:
            cursor.execute('''
                INSERT INTO finance_forecast (
                    service_name, renewal_date, monthly_cost, 
                    yearly_total, category
                ) VALUES (?, ?, ?, ?, ?)
            ''', (service_name, renewal_date, monthly_cost, yearly_total, category))
            conn.commit()
            flash('Subscription added successfully!')
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                flash('Database is currently locked. Please try again later.', 'error')
            else:
                flash(f'Error adding subscription: {str(e)}', 'error')
    
    try:
        cursor.execute('''
            SELECT id, service_name, renewal_date, monthly_cost, yearly_total, category 
            FROM finance_forecast 
            ORDER BY renewal_date
        ''')
        subscriptions = cursor.fetchall()
        
        total_monthly = sum(sub[3] for sub in subscriptions) if subscriptions else 0
        total_yearly = sum(sub[4] for sub in subscriptions) if subscriptions else 0
        
        cursor.execute('''
            SELECT category, SUM(monthly_cost) as total
            FROM finance_forecast 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY total DESC
        ''')
        category_totals = [{"name": row[0], "value": float(row[1])} for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT SUM(monthly_cost)
            FROM finance_forecast 
            WHERE category IS NULL
        ''')
        null_total = cursor.fetchone()[0]
        if null_total:
            category_totals.append({"name": "Other", "value": float(null_total)})

    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
            flash('Database is currently locked. Please try again later.', 'error')
        else:
            flash(f'Error fetching subscriptions: {str(e)}', 'error')
        subscriptions = []
        total_monthly = 0
        total_yearly = 0
        category_totals = []

    finally:
        conn.close()
    
    return render_template('finance_forecast.html',
                         subscriptions=subscriptions,
                         total_monthly=total_monthly,
                         total_yearly=total_yearly,
                         category_totals=category_totals)

@app.route('/add_pomodoro_type', methods=['POST'])
@login_required
def add_pomodoro_type():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        type_name = data.get('type_name')
        if not type_name or not type_name.strip():
            return jsonify({'error': 'Type name is required'}), 400
            
        type_name = type_name.strip()
        
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        try:
            # ...existing code...
            cursor.execute('SELECT type_name FROM pomodoro_types WHERE type_name = ?', (type_name,))
            if cursor.fetchone():
                return jsonify({'error': 'Pomodoro type already exists'}), 400
                
            # ...existing code...
            cursor.execute('INSERT INTO pomodoro_types (type_name) VALUES (?)', (type_name,))
            conn.commit()
            
            return jsonify({'success': True, 'type_name': type_name})
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Pomodoro type already exists'}), 400
            
    except Exception as e:
        app.logger.error(f'Error adding pomodoro type: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        cursor.close()
        conn.close()

@app.route('/log_pomodoro_session', methods=['POST'])
@login_required
def log_pomodoro_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # ...existing code...
        type_name = data.get('type')
        duration = data.get('duration')
        break_duration = data.get('break_duration')
        distractions = data.get('distractions', 0)
        notes = data.get('notes', '')

        # ...existing code...
        if not type_name or not duration:
            return jsonify({'error': 'Type and duration are required'}), 400

        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO pomodoro_stats (
                    date, type, duration, distractions, break_duration, notes
                ) VALUES (
                    date('now'), ?, ?, ?, ?, ?
                )
            ''', (type_name, duration, distractions, break_duration, notes))
            
            conn.commit()
            return jsonify({'success': True})

        except sqlite3.IntegrityError as e:
            return jsonify({'error': 'Database error: ' + str(e)}), 400
            
    except Exception as e:
        app.logger.error(f'Error logging Pomodoro session: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        cursor.close()
        conn.close()

@app.route('/update_work_log', methods=['POST'])
@login_required
def update_work_log():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        log_id = data.get('id')
        project = data.get('project')
        description = data.get('description')
        hours = data.get('hours')

        if not all([log_id, project, hours]):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            hours = float(hours)
        except ValueError:
            return jsonify({'error': 'Invalid hours value'}), 400

        conn = pkm.get_db_connection()
        cursor = conn.cursor()

        try:
            # ...existing code...
            cursor.execute('INSERT OR IGNORE INTO projects (name) VALUES (?)', (project,))
            cursor.execute('SELECT id FROM projects WHERE name = ?', (project,))
            project_id = cursor.fetchone()[0]

            # ...existing code...
            cursor.execute('''
                UPDATE work_logs 
                SET project_id = ?, description = ?, total_hours = ?
                WHERE id = ?
            ''', (project_id, description, hours, log_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Work log not found'}), 404

            conn.commit()
            return jsonify({'success': True})

        except sqlite3.Error as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
            
    except Exception as e:
        app.logger.error(f'Error updating work log: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/add_medication', methods=['POST'])
@login_required
def add_medication():
    try:
        name = request.form.get('name')
        dosage = request.form.get('dosage')
        frequency = request.form.get('frequency')
        time_of_day = request.form.get('time_of_day')
        notes = request.form.get('notes', '')
        refill_date = request.form.get('refill_date', '')

        if not all([name, dosage, frequency, time_of_day]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('medications'))

        conn = pkm.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO medications (
                name, dosage, frequency, time_of_day, 
                notes, refill_date, active
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (name, dosage, frequency, time_of_day, notes, refill_date))
        
        conn.commit()
        flash('Medication added successfully!', 'success')
        
    except sqlite3.IntegrityError:
        flash('A medication with this name already exists', 'error')
    except Exception as e:
        flash(f'Error adding medication: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('medications'))

@app.route('/metrics')
@login_required
def metrics():
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        chart_data = {
            'dates': [],
            'moods': [],
            'energies': [],
            'notes': []
        }
        
        # Update query to use correct column names
        cursor.execute('''
            SELECT 
                date,
                time,
                mood_level,
                energy_level,
                notes
            FROM sub_mood_logs 
            WHERE date >= date('now', '-30 days')
            ORDER BY date ASC, time ASC
        ''')
        
        logs = cursor.fetchall()
        app.logger.debug(f"Raw logs data: {logs}")
        
        if logs:
            # Process data with error checking
            try:
                dates = []
                moods = []
                energies = []
                notes = []
                
                current_date = None
                day_moods = []
                day_energies = []
                
                for log in logs:
                    log_date = log[0]
                    mood = log[2]
                    energy = log[3]
                    note = log[4]
                    
                    app.logger.debug(f"Processing log: date={log_date}, mood={mood}, energy={energy}")
                    
                    if current_date != log_date:
                        if current_date is not None:
                            # Calculate averages for previous day
                            avg_mood = sum(day_moods) / len(day_moods)
                            avg_energy = sum(day_energies) / len(day_energies)
                            
                            dates.append(current_date)
                            moods.append(round(avg_mood, 1))
                            energies.append(round(avg_energy, 1))
                            notes.append(", ".join(notes))
                            
                            app.logger.debug(f"Added day: {current_date}, mood={avg_mood}, energy={avg_energy}")
                        
                        # Reset for new day
                        current_date = log_date
                        day_moods = []
                        day_energies = []
                        notes = []
                    
                    if mood is not None:
                        day_moods.append(float(mood))
                    if energy is not None:
                        day_energies.append(float(energy))
                    if note:
                        notes.append(note)
                
                # Don't forget the last day
                if current_date is not None and day_moods:
                    avg_mood = sum(day_moods) / len(day_moods)
                    avg_energy = sum(day_energies) / len(day_energies)
                    
                    dates.append(current_date)
                    moods.append(round(avg_mood, 1))
                    energies.append(round(avg_energy, 1))
                    notes.append(", ".join(notes))
                
                chart_data = {
                    'dates': dates,
                    'moods': moods,
                    'energies': energies,
                    'notes': notes
                }
                
                app.logger.debug(f"Final chart_data: {chart_data}")
                
            except Exception as e:
                app.logger.error(f"Error processing log data: {str(e)}")
                raise
        
        # Calculate weekly averages
        cursor.execute('''
            SELECT 
                AVG(mood_level) as avg_mood,
                AVG(energy_level) as avg_energy
            FROM sub_mood_logs
            WHERE date >= date('now', '-7 days')
        ''')
        weekly_data = cursor.fetchone()
        weekly_averages = {
            'mood': round(weekly_data[0], 1) if weekly_data[0] else 0,
            'energy': round(weekly_data[1], 1) if weekly_data[1] else 0
        }
        
        # Get recent logs for display
        cursor.execute('''
            SELECT 
                id, date, time, mood_level, energy_level,
                activity, notes 
            FROM sub_mood_logs 
            ORDER BY date DESC, time DESC 
            LIMIT 10
        ''')
        submood_logs = [dict(zip(
            ['id', 'date', 'time', 'mood_level', 'energy_level', 'activity', 'notes'], 
            row)) for row in cursor.fetchall()]
        
        return render_template('metrics.html',
                             chart_data=chart_data,
                             weekly_averages=weekly_averages,
                             submood_logs=submood_logs,
                             selected_date=datetime.now().strftime('%Y-%m-%d'))
                             
    except Exception as e:
        app.logger.error(f"Error in metrics route: {str(e)}", exc_info=True)
        return render_template('metrics.html',
                             error=str(e),
                             chart_data={'dates':[], 'moods':[], 'energies':[], 'notes':[]},
                             weekly_averages={'mood':0, 'energy':0},
                             submood_logs=[],
                             selected_date=datetime.now().strftime('%Y-%m-%d'))
    finally:
        cursor.close()
        conn.close()

@app.route('/work', methods=['GET', 'POST'])
@login_required
def work():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        project = request.form.get('project')
        new_project = request.form.get('new_project_input')
        description = request.form.get('description')
        hours = float(request.form.get('hours', 0))
        
        # ...existing code...
        if project == 'new':
            project = new_project

        try:
            # ...existing code...
            cursor.execute('INSERT OR IGNORE INTO projects (name) VALUES (?)', (project,))
            cursor.execute('SELECT id FROM projects WHERE name = ?', (project,))
            project_id = cursor.fetchone()[0]
            
            # ...existing code...
            cursor.execute('''
                INSERT INTO work_logs (date, project_id, description, total_hours)
                VALUES (date('now'), ?, ?, ?)
            ''', (project_id, description, hours))
            
            conn.commit()
            flash('Work hours logged successfully!')
            
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                flash('Database is currently locked. Please try again later.', 'error')
            else:
                flash(f'Error logging work hours: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error logging work hours: {str(e)}')

    # ...existing code...
    cursor.execute('''
        SELECT id, name 
        FROM projects 
        ORDER BY name
    ''')
    existing_projects = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    # ...existing code...
    cursor.execute('''
        SELECT w.id, w.date, p.name as project, w.description, w.total_hours
        FROM work_logs w
        JOIN projects p ON w.project_id = p.id
        ORDER BY w.date DESC, w.created_at DESC
        LIMIT 10
    ''')
    work_logs = [dict(zip(['id', 'date', 'project', 'description', 'hours'], row)) 
                 for row in cursor.fetchall()]

    # ...existing code...
    cursor.execute('SELECT type_name FROM pomodoro_types ORDER BY type_name')
    pomodoro_types = [row[0] for row in cursor.fetchall()]
    
    # ...existing code...
    cursor.execute('''
        SELECT date, type, duration, break_duration, distractions, notes
        FROM pomodoro_stats
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    pomodoro_stats = [dict(zip(
        ['date', 'type', 'duration', 'break_duration', 'distractions', 'notes'], 
        row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('work.html',
                         existing_projects=existing_projects,
                         work_logs=work_logs,
                         pomodoro_types=pomodoro_types,
                         pomodoro_stats=pomodoro_stats)

@app.route('/log_sub_mood', methods=['POST'])
@login_required
def log_sub_mood():
    try:
        date = request.form.get('mood_date')
        time = request.form.get('mood_time')
        mood_level = int(request.form.get('mood_level'))
        energy_level = int(request.form.get('energy_level'))
        activity = request.form.get('activity')
        notes = request.form.get('notes')
        period = get_day_period()
        
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        # Updated query to match table schema
        cursor.execute('''
            INSERT INTO sub_mood_logs 
            (date, time, period, mood_level, energy_level, activity, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, time, period, mood_level, energy_level, activity, notes))
        
        conn.commit()
        flash('Mood logged successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
            
        return redirect(url_for('metrics'))
        
    except Exception as e:
        app.logger.error(f'Error logging mood: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 500
        flash(f'Error logging mood: {str(e)}')
        return redirect(url_for('metrics'))
    finally:
        cursor.close()
        conn.close()

@app.route('/add_anxiety_trigger', methods=['POST'])
@login_required
def add_anxiety_trigger():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
            
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400

        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO anxiety_triggers (name) VALUES (?)', (name,))
        conn.commit()
        trigger_id = cursor.lastrowid
        
        # ...existing code...
        return jsonify({
            'success': True,
            'trigger': {
                'id': trigger_id,
                'name': name
            }
        })

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Trigger already exists'}), 400
    except Exception as e:
        app.logger.error(f'Error adding anxiety trigger: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/add_coping_strategy', methods=['POST'])
@login_required
def add_coping_strategy():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
            
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400
            
        description = data.get('description', '').strip()

        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO coping_strategies (name, description) VALUES (?, ?)', 
                      (name, description))
        conn.commit()
        strategy_id = cursor.lastrowid
        
        # ...existing code...
        return jsonify({
            'success': True,
            'strategy': {
                'id': strategy_id,
                'name': name,
                'description': description
            }
        })

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Strategy already exists'}), 400
    except Exception as e:
        app.logger.error(f'Error adding coping strategy: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get_work_data')
@login_required
def get_work_data():
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        periods = {
            'daily': "date('now')",
            'weekly': "date('now', '-7 days')",
            'monthly': "date('now', '-30 days')",
            'yearly': "date('now', '-365 days')"
        }
        
        work_data = {}
        
        for period, date_filter in periods.items():
            cursor.execute(f'''
                SELECT p.name as project, SUM(w.total_hours) as total_hours
                FROM work_logs w
                JOIN projects p ON w.project_id = p.id
                WHERE w.date >= {date_filter}
                GROUP BY p.name
                ORDER BY total_hours DESC
            ''')
            
            rows = cursor.fetchall()
            work_data[period] = {
                'projects': [row[0] for row in rows],
                'total_hours': [float(row[1]) for row in rows]
            }
        
        return jsonify(work_data)
        
    except Exception as e:
        app.logger.error(f'Error fetching work data: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_work_log', methods=['POST'])
@login_required
def delete_work_log():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        log_id = data['id']

        conn = pkm.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM work_logs WHERE id = ?', (log_id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Work log not found'}), 404

        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f'Error deleting work log: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get_finance_trends')
@login_required
def get_finance_trends():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        
        # ...existing code...
        cursor.execute('''
            SELECT renewal_date, monthly_cost 
            FROM finance_forecast 
            ORDER BY renewal_date ASC
        ''')
        
        subscriptions = cursor.fetchall()
        
        # ...existing code...
        today = datetime.now()
        start_date = today - timedelta(days=365)
        end_date = today + timedelta(days=365)
        
        dates = []
        historical = []
        projected = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            monthly_total = sum(float(sub[1]) for sub in subscriptions 
                              if datetime.strptime(sub[0], '%Y-%m-%d') <= current_date)
            
            if current_date <= today:
                historical.append(monthly_total)
                projected.append(None)
            else:
                historical.append(None)
                projected.append(monthly_total)
                
            current_date += timedelta(days=30)
        
        total_spent = sum(h for h in historical if h is not None)
        future_monthly = projected[0] if projected else 0
        
        return jsonify({
            'dates': dates,
            'historical': historical,
            'projected': projected,
            'totalSpent': total_spent,
            'futureMonthly': future_monthly
        })
        
    except Exception as e:
        app.logger.error(f'Error in get_finance_trends: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        if conn:
            conn.close()

@app.route('/get_anxiety_triggers')
@login_required
def get_anxiety_triggers():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM anxiety_triggers ORDER BY name')
        triggers = cursor.fetchall()
        return jsonify([{'id': t[0], 'name': t[1]} for t in triggers])
    except Exception as e:
        app.logger.error(f'Error fetching anxiety triggers: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_coping_strategies')
@login_required
def get_coping_strategies():
    try:
        conn = pkm.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM coping_strategies ORDER BY name')
        strategies = cursor.fetchall()
        return jsonify([{'id': s[0], 'name': s[1]} for s in strategies])
    except Exception as e:
        app.logger.error(f'Error fetching coping strategies: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_current_datetime')
@login_required
def get_current_datetime():
    try:
        now = datetime.now()
        return jsonify({
            'success': True,
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M'),
            'timestamp': now.strftime('%Y-%m-%dT%H:%M')  # Added ISO format for proper input fields
        })
    except Exception as e:
        app.logger.error(f'Error getting current datetime: {str(e)}')
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PKM Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to listen on')
    args = parser.parse_args()
    
    config = load_config()
    if not config['web_enabled']:
        print("Web interface is disabled. Enable it in web/config.json")
    else:
        port = args.port if args.port else config.get('port', 5000)
        with app.app_context():
            init_db()
        app.run(host=args.host, port=port, debug=True)