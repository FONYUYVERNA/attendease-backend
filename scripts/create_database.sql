-- Create the AttendEase database
-- Run this in pgAdmin or psql as a superuser

-- Create database
CREATE DATABASE attendease;

-- Create a user for the application (optional but recommended)
-- Replace 'attendease_user' and 'your_password' with your preferred credentials
CREATE USER attendease_user WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE attendease TO attendease_user;

-- Connect to the attendease database and grant schema privileges
\c attendease;
GRANT ALL ON SCHEMA public TO attendease_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO attendease_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO attendease_user;

-- Grant future privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO attendease_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO attendease_user;
