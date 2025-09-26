-- Create database and user for Afaq School application
CREATE DATABASE IF NOT EXISTS afaqschool1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user for the application (more secure than using root)
CREATE USER IF NOT EXISTS 'afaqschool_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON afaqschool1.* TO 'afaqschool_user'@'localhost';
FLUSH PRIVILEGES;

-- Use the database
USE afaqschool1;

-- Create tables (this will be imported from your existing afaqschool.sql file)
-- The main tables are:
-- - applications
-- - donations  
-- - payments
-- - students
-- - users
