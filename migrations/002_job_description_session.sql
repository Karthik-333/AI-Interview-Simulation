-- Add the optional raw job description to interview sessions.
ALTER TABLE interview_sessions ADD COLUMN job_description TEXT;
