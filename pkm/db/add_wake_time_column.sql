-- Migration to add wake_time column to daily_metrics table
ALTER TABLE daily_metrics ADD COLUMN wake_time TIMESTAMP;
