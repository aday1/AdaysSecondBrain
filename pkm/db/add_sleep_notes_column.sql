-- Migration to add sleep_notes column to daily_metrics table
ALTER TABLE daily_metrics ADD COLUMN sleep_notes TEXT;
