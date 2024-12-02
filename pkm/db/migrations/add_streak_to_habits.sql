-- Migration script to add streak column to habits table
ALTER TABLE habits ADD COLUMN streak INTEGER DEFAULT 0;
