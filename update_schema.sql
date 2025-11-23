-- Drop existing tables in reverse order of creation to handle dependencies
DROP TABLE IF EXISTS diagnostic_results;
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;

-- Re-enable the uuid-ossp extension if it exists, otherwise create it
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for user authentication, directly related to /api/signup and /api/login
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store metadata about HTML files (for future use)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for logging results from diagnostic tools, directly related to /api/ping, /api/port_scan, /api/traceroute
CREATE TABLE diagnostic_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL, -- e.g., 'ping', 'port_scan', 'traceroute'
    target TEXT NOT NULL, -- e.g., 'google.com', '1.1.1.1:443'
    summary TEXT, -- A brief, human-readable result
    raw_log TEXT, -- The full, raw output from the tool
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for tracking incidents (for future use)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    narrative TEXT,
    status TEXT NOT NULL, -- e.g., 'active', 'watching', 'resolved'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing contact form submissions, related to /api/contact
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Create indexes for foreign keys and frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_diagnostic_results_user_id ON diagnostic_results(user_id);
CREATE INDEX idx_incidents_status ON incidents(status);

-- Create a vector column for Full-Text Search on documents
ALTER TABLE documents ADD COLUMN fts_vector tsvector;

-- Create a function to update the fts_vector column
CREATE OR REPLACE FUNCTION update_documents_fts_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fts_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update the fts_vector on insert or update
CREATE TRIGGER documents_fts_update
BEFORE INSERT OR UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION update_documents_fts_vector();

-- Create a GIN index for Full-Text Search
CREATE INDEX idx_documents_fts ON documents USING GIN(fts_vector);
