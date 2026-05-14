"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enum types — safe to re-run
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tool_type_enum AS ENUM ('builtin', 'custom');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE run_status_enum AS ENUM ('running', 'completed', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # Tables — all use IF NOT EXISTS so restarts are safe
    op.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            tool_type   tool_type_enum NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            config      JSONB,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS deep_agents (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            description   TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            model         TEXT NOT NULL DEFAULT 'gpt-4o',
            temperature   FLOAT NOT NULL DEFAULT 0.0,
            created_at    TIMESTAMP NOT NULL DEFAULT now(),
            updated_at    TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sub_agents (
            id            TEXT PRIMARY KEY,
            deep_agent_id TEXT NOT NULL REFERENCES deep_agents(id) ON DELETE CASCADE,
            name          TEXT NOT NULL,
            description   TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            model         TEXT,
            created_at    TIMESTAMP NOT NULL DEFAULT now(),
            updated_at    TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_tools (
            agent_id TEXT NOT NULL REFERENCES deep_agents(id) ON DELETE CASCADE,
            tool_id  TEXT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
            PRIMARY KEY (agent_id, tool_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS subagent_tools (
            subagent_id TEXT NOT NULL REFERENCES sub_agents(id) ON DELETE CASCADE,
            tool_id     TEXT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
            PRIMARY KEY (subagent_id, tool_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id           TEXT PRIMARY KEY,
            agent_id     TEXT NOT NULL REFERENCES deep_agents(id) ON DELETE CASCADE,
            input        TEXT NOT NULL,
            output       TEXT NOT NULL DEFAULT '',
            status       run_status_enum NOT NULL DEFAULT 'running',
            steps        JSONB,
            created_at   TIMESTAMP NOT NULL DEFAULT now(),
            completed_at TIMESTAMP
        )
    """)

    # Seed built-in tools — ON CONFLICT DO NOTHING makes this idempotent
    op.execute("""
        INSERT INTO tools (id, name, tool_type, description) VALUES
        (gen_random_uuid()::text, 'write_todos', 'builtin', 'Manage a todo/planning list'),
        (gen_random_uuid()::text, 'ls',          'builtin', 'List directory contents'),
        (gen_random_uuid()::text, 'read_file',   'builtin', 'Read a file from the filesystem'),
        (gen_random_uuid()::text, 'write_file',  'builtin', 'Write content to a file'),
        (gen_random_uuid()::text, 'edit_file',   'builtin', 'Edit an existing file'),
        (gen_random_uuid()::text, 'glob',        'builtin', 'Find files by glob pattern'),
        (gen_random_uuid()::text, 'grep',        'builtin', 'Search file contents with regex'),
        (gen_random_uuid()::text, 'execute',     'builtin', 'Execute shell commands (requires sandbox backend)'),
        (gen_random_uuid()::text, 'task',        'builtin', 'Delegate work to a sub-agent')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_runs")
    op.execute("DROP TABLE IF EXISTS subagent_tools")
    op.execute("DROP TABLE IF EXISTS agent_tools")
    op.execute("DROP TABLE IF EXISTS sub_agents")
    op.execute("DROP TABLE IF EXISTS deep_agents")
    op.execute("DROP TABLE IF EXISTS tools")
    op.execute("DROP TYPE IF EXISTS tool_type_enum")
    op.execute("DROP TYPE IF EXISTS run_status_enum")
