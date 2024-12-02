-- Drop existing backup table if it exists
DROP TABLE IF EXISTS work_logs_backup;

-- Backup existing work_logs table
CREATE TABLE work_logs_backup AS SELECT * FROM work_logs;

-- Drop existing work_logs table
DROP TABLE IF EXISTS work_logs;

-- Create projects table if not exists
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recreate work_logs table with project_id
CREATE TABLE work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    project_id INTEGER,
    description TEXT,
    total_hours FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Add bedtime column to daily_metrics table
ALTER TABLE daily_metrics ADD COLUMN bedtime TIMESTAMP;

-- Add wake_time column to daily_metrics table
ALTER TABLE daily_metrics ADD COLUMN wake_time TIMESTAMP;

-- Insert unique project names from backup
INSERT OR IGNORE INTO projects (name)
SELECT DISTINCT name FROM work_logs_backup;  -- Adjusted to use name instead of project_id

-- Restore data with project_id references
INSERT INTO work_logs (date, project_id, description, total_hours, created_at)
SELECT 
    wb.date,
    wb.project_id,
    wb.description,
    wb.total_hours,
    wb.created_at
FROM work_logs_backup wb;

-- Drop backup table
DROP TABLE work_logs_backup;
