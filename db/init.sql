-- Core tables for personal metrics tracking

-- Habits tracking
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL, -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    streak INTEGER DEFAULT 0  -- Added streak column directly here
);

-- Routine tracking
CREATE TABLE IF NOT EXISTS routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL, -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Work hours tracking
CREATE TABLE IF NOT EXISTS work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    project TEXT,
    description TEXT,
    total_hours FLOAT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily metrics for general tracking
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    sleep_hours FLOAT,
    sleep_notes TEXT,
    sleep_quality TEXT,
    bed_time TIMESTAMP,
    wake_up_time TIMESTAMP,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sub-daily mood tracking for more granular metrics
CREATE TABLE IF NOT EXISTS sub_mood_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    mood_level INTEGER CHECK (mood_level BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    activity TEXT,
    notes TEXT,
    type TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Goals and plans
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    target_date DATE,
    status TEXT DEFAULT 'active',
    completion INTEGER DEFAULT 0, -- New column for completion percentage
    notes TEXT, -- New column for notes
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
    yearly_total FLOAT, -- Removed default value
    category TEXT -- Allowing this to be empty until user creates categories
);

-- Medication tracking tables
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    time_of_day TEXT NOT NULL,
    notes TEXT,
    refill_date DATE,  -- Added refill_date column
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

-- Clear existing data from daily_metrics
DELETE FROM daily_metrics;

-- Insert initial data into daily_metrics
INSERT INTO daily_metrics (date, mood_rating, energy_level) VALUES
('2024-01-01', 1, 1),
('2023-01-01', 1, 1),
('2022-01-01', 1, 1);

-- Insert initial data into sub_mood_logs with default values
INSERT INTO sub_mood_logs (date, timestamp, mood_level, energy_level, type)
VALUES ('2024-01-01', CURRENT_TIMESTAMP, 1, 1, 'default_type');
