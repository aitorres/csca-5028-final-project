CREATE TYPE post_source AS ENUM ('bluesky', 'user');
CREATE TYPE post_sentiment_type AS ENUM ('positive', 'neutral', 'negative');

CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source post_source NOT NULL,
    content TEXT NOT NULL,
    sentiment post_sentiment_type NOT NULL
);

CREATE INDEX idx_posts_created_at ON posts (created_at);
CREATE INDEX idx_posts_source ON posts (source);
CREATE INDEX idx_posts_sentiment ON posts (sentiment);
