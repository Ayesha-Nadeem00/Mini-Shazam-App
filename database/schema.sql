-- ============================================
-- Shazam-like App: Database Schema
-- Database: PostgreSQL
-- Limit: 500 songs (app-level limit, DB khud enforce nahi karta)
-- ============================================

-- 1) Songs table: har song ki basic info
CREATE TABLE songs (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    artist      VARCHAR(255) NOT NULL,
    album       VARCHAR(255),
    duration_sec INTEGER,              -- song ki total length (seconds mein)
    stream_link TEXT,                  -- Spotify/YouTube link (optional)
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 2) Fingerprints table: har song ke hash points
-- Ek song ke sainkron (hundreds/thousands) fingerprint rows ho sakte hain
CREATE TABLE fingerprints (
    id          BIGSERIAL PRIMARY KEY,
    song_id     INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    hash        BIGINT NOT NULL,       -- freq1+freq2+time-delta se bana hua hash
    time_offset FLOAT NOT NULL         -- is hash ka original song mein waqt (seconds)
);

-- ============================================
-- IMPORTANT: Ye index sabse zaroori hai!
-- Matching ke waqt hum "hash" pe hi search karte hain
-- lakhon rows mein se — bina index ke ye BOHOT slow hoga.
-- ============================================
CREATE INDEX idx_fingerprints_hash ON fingerprints(hash);

-- Optional: agar app-level pe 500 songs ki limit check karni ho,
-- to backend code mein query se count check karein, jaise:
-- SELECT COUNT(*) FROM songs;
-- agar count >= 500 ho to naya insert allow na karein.
