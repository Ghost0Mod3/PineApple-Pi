PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'administrator',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,user_id INTEGER,event TEXT NOT NULL,message TEXT NOT NULL,details TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS authorization_sessions(id TEXT PRIMARY KEY,state TEXT NOT NULL,expires_at TEXT NOT NULL,tools_json TEXT NOT NULL,targets_json TEXT NOT NULL,snapshot_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tool_jobs(id TEXT PRIMARY KEY,tool_id TEXT NOT NULL,user_id INTEGER NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL,finished_at TEXT,config_json TEXT NOT NULL,artifact_dir TEXT NOT NULL,return_code INTEGER,summary TEXT);
