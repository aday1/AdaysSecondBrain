
-- Create temporary table with new schema
CREATE TABLE work_logs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    project_id INTEGER,
    description TEXT,
    total_hours FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Migrate existing data
INSERT INTO work_logs_new (date, project_id, description, total_hours, created_at)
SELECT 
    w.date,
    COALESCE(p.id, (SELECT id FROM projects WHERE name = w.project)), -- Try to match existing project names
    w.description,
    w.total_hours,
    w.created_at
FROM work_logs w
LEFT JOIN projects p ON w.project = p.name;

-- Drop old table and rename new one
DROP TABLE work_logs;
ALTER TABLE work_logs_new RENAME TO work_logs;

-- Create index for better query performance
CREATE INDEX idx_work_logs_project_id ON work_logs(project_id);