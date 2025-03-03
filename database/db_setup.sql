CREATE TABLE fingerprint_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE, 
    template BYTEA NOT NULL 
);
