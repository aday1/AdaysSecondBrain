-- Migration to add bedtime column to daily_metrics table
ALTER TABLE daily_metrics ADD COLUMN bedtime TIMESTAMP;
