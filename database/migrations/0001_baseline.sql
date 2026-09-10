PRAGMA foreign_keys = ON;

CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT NOT NULL ,
    subject_name TEXT NOT NULL,
    scheme TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    UNIQUE(subject_code, scheme, department, semester)
);

CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    module_no INTEGER NOT NULL,
    module_title TEXT NOT NULL,
    UNIQUE(subject_id, module_no),
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    topic_name TEXT NOT NULL,
    UNIQUE(module_id, topic_name),
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS pyq_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    module_no INTEGER,
    marks INTEGER,
    question_text TEXT NOT NULL,
    topic_id INTEGER,
    topic_name TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

CREATE TABLE if NOT EXISTS topic_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL UNIQUE,
    frequency INTEGER NOT NULL DEFAULT 0,
    weighted_score REAL NOT NULL DEFAULT 0,
    importance_level TEXT NOT NULL CHECK (importance_level IN ('High', 'Medium', 'Low')),
    last_asked_year INTEGER,
    probability_score REAL NOT NULL DEFAULT 0,
    probability_label TEXT NOT NULL DEFAULT 'Low',
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Per-module ranking of topics by PYQ weight, rebuilt by
-- src/module_topic_priority_engine.py::rebuild_module_topic_priority()
CREATE TABLE if NOT EXISTS module_topic_priority (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    module_no INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    question_count INTEGER NOT NULL DEFAULT 0,
    weighted_score REAL NOT NULL DEFAULT 0,
    priority_label TEXT NOT NULL CHECK (priority_label IN ('High', 'Medium', 'Low')),
    UNIQUE(subject_id, module_no, topic_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Per-user engagement log, written by src/progress_engine.py::log_topic_activity()
CREATE TABLE if NOT EXISTS topic_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    activity_value TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('not_started', 'in_progress', 'completed', 'weak')),
    last_updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, topic_id),
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    exam_date TEXT,
    hours_per_day REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS study_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_plan_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    plan_date TEXT NOT NULL,
    priority_score REAL NOT NULL DEFAULT 0,
    recommended_hours REAL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'skipped')),
    FOREIGN KEY (study_plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subject_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);

CREATE TABLE if NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE TABLE if NOT EXISTS image_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subject_id INTEGER,
    image_path TEXT,
    extracted_text TEXT,
    mapped_topic_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (mapped_topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

CREATE INDEX idx_subjects_department_semester ON subjects(department, semester);
CREATE INDEX idx_modules_subject_id ON modules(subject_id);
CREATE INDEX idx_topics_module_id ON topics(module_id);
CREATE INDEX idx_pyq_subject_year ON pyq_questions(subject_id, year);
CREATE INDEX idx_pyq_topic_id ON pyq_questions(topic_id);
CREATE INDEX idx_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_plan_items_plan_id ON study_plan_items(study_plan_id);
CREATE INDEX idx_chat_session_user ON chat_sessions(user_id);
CREATE INDEX idx_module_topic_priority_subject_module ON module_topic_priority(subject_id, module_no);
CREATE INDEX idx_topic_activity_user_id ON topic_activity(user_id);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    scheme TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Login tokens issued by src/session_store.py. Keyed by a random URL token
-- (not a shared file) so concurrent users on a hosted deployment each keep
-- their own session.
CREATE TABLE IF NOT EXISTS auth_sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);