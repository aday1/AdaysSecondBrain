-- Core anxiety tracking tables
CREATE TABLE IF NOT EXISTS anxiety_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS coping_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS anxiety_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time_started TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    suds_score INTEGER NOT NULL CHECK (suds_score BETWEEN 1 AND 10),
    social_isolation INTEGER CHECK (social_isolation BETWEEN 0 AND 10),
    insufficient_self_control INTEGER CHECK (insufficient_self_control BETWEEN 0 AND 10),
    subjugation INTEGER CHECK (subjugation BETWEEN 0 AND 10),
    negativity INTEGER CHECK (negativity BETWEEN 0 AND 10),
    unrelenting_standards INTEGER CHECK (unrelenting_standards BETWEEN 0 AND 10),
    trigger_id INTEGER,
    coping_strategy_id INTEGER,
    effectiveness INTEGER CHECK (effectiveness BETWEEN 1 AND 10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trigger_id) REFERENCES anxiety_triggers(id),
    FOREIGN KEY (coping_strategy_id) REFERENCES coping_strategies(id)
);

-- Verify the table structure
.schema anxiety_logs;

-- Show the columns
.headers on
.mode column
PRAGMA table_info(anxiety_logs);

-- Add some initial test data
INSERT OR IGNORE INTO anxiety_triggers (name) VALUES 
    ('Work Deadline'),
    ('Social Situation'),
    ('Health Concern');

INSERT OR IGNORE INTO coping_strategies (name) VALUES 
    ('Deep Breathing'),
    ('Progressive Relaxation'),
    ('Mindful Walking');