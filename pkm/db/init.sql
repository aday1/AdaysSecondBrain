-- Core tables for personal metrics tracking

-- Create tables only if they don't exist - REMOVE all DROP statements
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    streak INTEGER DEFAULT 0
);

-- Routine tracking
CREATE TABLE IF NOT EXISTS routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    routine_time TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL,
    day TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- Habit logs for tracking completion
CREATE TABLE IF NOT EXISTS habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (habit_id) REFERENCES habits(id)
);

-- Alcohol consumption tracking
CREATE TABLE IF NOT EXISTS alcohol_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    drink_type TEXT NOT NULL,
    units FLOAT NOT NULL,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table first
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add default project
INSERT OR IGNORE INTO projects (name, description) 
VALUES ('General', 'Default project for work logs');

-- Create work logs table
CREATE TABLE IF NOT EXISTS work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    project_id INTEGER,
    description TEXT,
    total_hours FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Create index for work logs
CREATE INDEX IF NOT EXISTS idx_work_logs_project_id ON work_logs(project_id);

-- Daily metrics for general tracking
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    sleep_hours FLOAT,
    sleep_notes TEXT,
    sleep_quality TEXT,
    bedtime TIMESTAMP,
    wake_time TIMESTAMP,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drop and recreate sub_mood_logs table
CREATE TABLE IF NOT EXISTS sub_mood_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time TEXT NOT NULL,
    period TEXT,
    mood_level INTEGER CHECK (mood_level BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    activity TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for sub_mood_logs
CREATE INDEX IF NOT EXISTS idx_submood_date ON sub_mood_logs(date);

-- Goals and plans
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    target_date DATE,
    status TEXT DEFAULT 'active',
    completion INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Daily entries for comprehensive daily logging
CREATE TABLE IF NOT EXISTS daily_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Finance forecast for managing subscriptions
CREATE TABLE IF NOT EXISTS finance_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    renewal_date DATE NOT NULL,
    monthly_cost FLOAT NOT NULL,
    yearly_total FLOAT,
    category TEXT
);

-- Medication tracking tables
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    time_of_day TEXT NOT NULL,
    notes TEXT,
    refill_date DATE,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medication_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    taken_at TIMESTAMP NOT NULL,
    taken BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medication_id) REFERENCES medications(id)
);

CREATE TABLE IF NOT EXISTS medication_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    reminder_time TIME NOT NULL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medication_id) REFERENCES medications(id)
);

-- Pomodoro tracking tables
CREATE TABLE IF NOT EXISTS pomodoro_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pomodoro_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    type TEXT NOT NULL,
    duration INTEGER NOT NULL,
    break_duration INTEGER,
    distractions INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type) REFERENCES pomodoro_types(type_name)
);

-- Add some default Pomodoro types
INSERT OR IGNORE INTO pomodoro_types (type_name) VALUES 
    ('Work'),
    ('Study'),
    ('Programming'),
    ('Writing'),
    ('Reading');

-- Anxiety tracking tables
CREATE TABLE IF NOT EXISTS anxiety_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS coping_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Anxiety logs tracking table
CREATE TABLE IF NOT EXISTS anxiety_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time_started TEXT NOT NULL,
    anxiety_level INTEGER CHECK (anxiety_level BETWEEN 1 AND 10),
    notes TEXT,
    unrelenting_standards INTEGER,
    duration_minutes INTEGER,
    suds_score INTEGER CHECK (suds_score BETWEEN 1 AND 10),
    social_isolation INTEGER,
    insufficient_self_control INTEGER,
    subjugation INTEGER,
    negativity INTEGER,
    trigger_id INTEGER,
    coping_strategy_id INTEGER,
    effectiveness INTEGER,
    FOREIGN KEY (trigger_id) REFERENCES anxiety_triggers(id),
    FOREIGN KEY (coping_strategy_id) REFERENCES coping_strategies(id)
);

-- Anxiety SUDS Tracking table
CREATE TABLE IF NOT EXISTS anxiety_suds_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    suds_score INTEGER NOT NULL CHECK (suds_score >= 1 AND suds_score <= 10),
    strategy TEXT,
    type_of_anxiety TEXT,
    anxiety_trigger TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add initial data AFTER table creation
INSERT OR IGNORE INTO anxiety_triggers (name) VALUES 
    ('Work Deadline'),
    ('Social Situation'),
    ('Health Concern');

INSERT OR IGNORE INTO coping_strategies (name) VALUES 
    ('Deep Breathing'),
    ('Progressive Relaxation'),
    ('Mindful Walking');

-- Gratitude tracking
CREATE TABLE IF NOT EXISTS gratitude (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Goal progress history
CREATE TABLE IF NOT EXISTS goal_progress_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    completion INTEGER NOT NULL,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals(id)
);
