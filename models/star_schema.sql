-- ====================================================================
-- PitchPulse 360 - Dimensional Data Modeling (Kimball Star Schema)
-- Syllabus CO4: Relational Schema Design, Normalization & Star Schema
-- ====================================================================

-- 1. Dimension: Teams
CREATE TABLE IF NOT EXISTS Dim_Teams (
    team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100),
    manager_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension: Players
CREATE TABLE IF NOT EXISTS Dim_Players (
    player_id INTEGER PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    current_team_id INTEGER REFERENCES Dim_Teams(team_id),
    primary_position VARCHAR(50),
    jersey_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Dimension: Matches
CREATE TABLE IF NOT EXISTS Dim_Matches (
    match_id VARCHAR(50) PRIMARY KEY,
    competition_name VARCHAR(100),
    season VARCHAR(20),
    match_date DATE,
    home_team_id INTEGER REFERENCES Dim_Teams(team_id),
    away_team_id INTEGER REFERENCES Dim_Teams(team_id),
    stadium VARCHAR(100),
    referee VARCHAR(100)
);

-- 4. Dimension: Event Types
CREATE TABLE IF NOT EXISTS Dim_Event_Types (
    event_type_id INTEGER PRIMARY KEY,
    event_type_name VARCHAR(50) NOT NULL,
    category VARCHAR(50) -- 'Offensive', 'Defensive', 'Set Piece', 'Disciplinary'
);

-- 5. Fact Table: Match Events (High-Granularity Fact Table)
CREATE TABLE IF NOT EXISTS Fact_Match_Events (
    event_surrogate_key BIGINT PRIMARY KEY,
    event_natural_id VARCHAR(100) UNIQUE,
    match_id VARCHAR(50) REFERENCES Dim_Matches(match_id),
    team_id INTEGER REFERENCES Dim_Teams(team_id),
    player_id INTEGER REFERENCES Dim_Players(player_id),
    event_type_id INTEGER REFERENCES Dim_Event_Types(event_type_id),
    period INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    second INTEGER NOT NULL,
    location_x FLOAT,
    location_y FLOAT,
    xg FLOAT DEFAULT 0.0,
    shot_outcome VARCHAR(50),
    pass_length FLOAT,
    is_successful_action BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Query Performance & Partitioning (Module 4.2)
CREATE INDEX IF NOT EXISTS idx_fact_match ON Fact_Match_Events(match_id);
CREATE INDEX IF NOT EXISTS idx_fact_player ON Fact_Match_Events(player_id);
CREATE INDEX IF NOT EXISTS idx_fact_minute ON Fact_Match_Events(match_id, period, minute);
