"""SQLite storage layer."""
import hashlib
import sqlite3


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, department TEXT NOT NULL,
    semester INTEGER NOT NULL, contact TEXT);
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, department TEXT, email TEXT, contact TEXT);
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL UNIQUE, department TEXT,
    faculty_id INTEGER REFERENCES faculty(faculty_id));
CREATE TABLE IF NOT EXISTS attendance (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Present','Absent')),
    UNIQUE (student_id, subject_id, date));
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin','Faculty','Student')),
    ref_id INTEGER);
"""


class Database:
    """Thin wrapper around sqlite3 used by AttendanceManager."""

    def __init__(self, path="attendance.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._seed_admin()

    def _seed_admin(self):
        if not self.query("SELECT 1 FROM users WHERE role='Admin'"):
            self.execute("INSERT INTO users VALUES (?,?,?,?)",
                         ("admin", hash_password("admin123"), "Admin", None))

    def execute(self, sql, params=()):
        """Run a write statement; returns the cursor (use .lastrowid)."""
        with self.conn:
            return self.conn.execute(sql, params)

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()
