-- Auto-generated from SQLAlchemy models (backend/app/models/).
-- Regenerate any time with the snippet in database/README.md.
-- Dialect shown: SQLite (the prototype default). See docs/DATABASE.md for the
-- one-line change to target PostgreSQL instead -- the SQLAlchemy models are
-- dialect-agnostic, so no model code changes are needed.

CREATE TABLE accounts (
	id VARCHAR(20) NOT NULL, 
	masked_number VARCHAR(32) NOT NULL, 
	institution VARCHAR(128) NOT NULL, 
	account_type VARCHAR(64) NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE alerts (
	id VARCHAR(20) NOT NULL, 
	case_id VARCHAR(20) NOT NULL, 
	entity_id VARCHAR(20) NOT NULL, 
	severity VARCHAR(16) NOT NULL, 
	detection_rule VARCHAR(64) NOT NULL, 
	label VARCHAR(64) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	evidence TEXT NOT NULL, 
	confidence FLOAT NOT NULL, 
	timestamp DATETIME NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	assigned_to VARCHAR(128) NOT NULL, 
	notes JSON NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE audit_logs (
	seq INTEGER NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	user_id VARCHAR(20) NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	event_data TEXT NOT NULL, 
	timestamp DATETIME NOT NULL, 
	previous_hash VARCHAR(64) NOT NULL, 
	current_hash VARCHAR(64) NOT NULL, 
	PRIMARY KEY (seq)
);

CREATE TABLE cases (
	id VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	category VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	priority VARCHAR(16) NOT NULL, 
	risk_level VARCHAR(16) NOT NULL, 
	region VARCHAR(64) NOT NULL, 
	assigned_investigator VARCHAR(128) NOT NULL, 
	opened_date DATE NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE events (
	id VARCHAR(20) NOT NULL, 
	case_id VARCHAR(20) NOT NULL, 
	event_type VARCHAR(32) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	timestamp DATETIME NOT NULL, 
	location_id VARCHAR(20) NOT NULL, 
	related_entities JSON NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE evidence (
	id VARCHAR(20) NOT NULL, 
	case_id VARCHAR(20) NOT NULL, 
	entity_id VARCHAR(20) NOT NULL, 
	evidence_type VARCHAR(64) NOT NULL, 
	description TEXT NOT NULL, 
	sha256_hash VARCHAR(64) NOT NULL, 
	source VARCHAR(128) NOT NULL, 
	uploaded_by VARCHAR(64) NOT NULL, 
	uploaded_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE locations (
	id VARCHAR(20) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	region VARCHAR(64) NOT NULL, 
	location_type VARCHAR(64) NOT NULL, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE organizations (
	id VARCHAR(20) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	org_type VARCHAR(64) NOT NULL, 
	region VARCHAR(64) NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE persons (
	id VARCHAR(20) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	gender VARCHAR(16) NOT NULL, 
	age_range VARCHAR(16) NOT NULL, 
	nationality VARCHAR(64) NOT NULL, 
	occupation VARCHAR(128) NOT NULL, 
	region VARCHAR(64) NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE phones (
	id VARCHAR(20) NOT NULL, 
	number VARCHAR(32) NOT NULL, 
	carrier VARCHAR(64) NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE relationships (
	id VARCHAR(20) NOT NULL, 
	source_id VARCHAR(20) NOT NULL, 
	source_type VARCHAR(32) NOT NULL, 
	target_id VARCHAR(20) NOT NULL, 
	target_type VARCHAR(32) NOT NULL, 
	relation_type VARCHAR(32) NOT NULL, 
	case_id VARCHAR(20) NOT NULL, 
	occurred_on DATE NOT NULL, 
	frequency INTEGER NOT NULL, 
	evidence VARCHAR(500) NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	confidence FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE users (
	id VARCHAR(20) NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	full_name VARCHAR(128) NOT NULL, 
	email VARCHAR(128) NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE vehicles (
	id VARCHAR(20) NOT NULL, 
	registration VARCHAR(32) NOT NULL, 
	vehicle_type VARCHAR(64) NOT NULL, 
	color VARCHAR(32) NOT NULL, 
	first_seen DATE NOT NULL, 
	last_seen DATE NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);
