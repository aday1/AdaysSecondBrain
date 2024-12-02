-- Add completion_rate field to habits table
ALTER TABLE habits 
ADD COLUMN completion_rate FLOAT DEFAULT 0;
