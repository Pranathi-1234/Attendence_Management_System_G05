"""Business logic: AttendanceManager sits between the GUI and the database."""
from database import Database, hash_password
from models import (Student, AttendanceRecord, ValidationError, DuplicateRecordError,
                    NotFoundError, AuthenticationError, validate_date)
from user import ROLE_CLASSES

LOW_ATTENDANCE_LIMIT = 75.0


class AttendanceManager:
    def __init__(self, db_path="attendance.db"):
        self.db = Database(db_path)

    # ---------- login ----------
    def authenticate(self, username, password):
        rows = self.db.query("SELECT * FROM users WHERE username=?", (username.strip(),))
        if not rows:
            raise AuthenticationError("Invalid username or password.")
        r = rows[0]
        user = ROLE_CLASSES[r["role"]](r["username"], r["password_hash"], r["ref_id"])
        if not user.check_password(password):
            raise AuthenticationError("Invalid username or password.")
        return user

    def _create_login(self, prefix, ref_id, role):
        username = f"{prefix}{ref_id}"
        self.db.execute("INSERT INTO users VALUES (?,?,?,?)",
                        (username, hash_password(username), role, ref_id))
        return username   # default password = username

    # ---------- students ----------
    def add_student(self, name, department, semester, contact=""):
        s = Student(None, name, department, semester, contact)   # validates input
        cur = self.db.execute(
            "INSERT INTO students (name, department, semester, contact) VALUES (?,?,?,?)",
            (s.name, s.department, s.semester, s.contact))
        return cur.lastrowid, self._create_login("stu", cur.lastrowid, "Student")

    def _row_to_student(self, r):
        return Student(r["student_id"], r["name"], r["department"], r["semester"], r["contact"])

    def get_student(self, student_id):
        rows = self.db.query("SELECT * FROM students WHERE student_id=?", (student_id,))
        if not rows:
            raise NotFoundError(f"Student {student_id} not found.")
        return self._row_to_student(rows[0])

    def list_students(self, text=""):
        like = f"%{text.strip()}%"
        rows = self.db.query(
            "SELECT * FROM students WHERE name LIKE ? OR department LIKE ? OR CAST(student_id AS TEXT) LIKE ? "
            "ORDER BY student_id", (like, like, like))
        return [self._row_to_student(r) for r in rows]

    def update_student(self, student_id, name, department, semester, contact=""):
        self.get_student(student_id)
        s = Student(student_id, name, department, semester, contact)
        self.db.execute("UPDATE students SET name=?, department=?, semester=?, contact=? WHERE student_id=?",
                        (s.name, s.department, s.semester, s.contact, student_id))

    def delete_student(self, student_id):
        self.get_student(student_id)
        self.db.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        self.db.execute("DELETE FROM users WHERE role='Student' AND ref_id=?", (student_id,))

    # ---------- faculty and subjects ----------
    def add_faculty(self, name, department="", email="", contact=""):
        if not name.strip():
            raise ValidationError("Faculty name cannot be empty.")
        cur = self.db.execute("INSERT INTO faculty (name, department, email, contact) VALUES (?,?,?,?)",
                              (name.strip(), department.strip(), email.strip(), contact.strip()))
        return cur.lastrowid, self._create_login("fac", cur.lastrowid, "Faculty")

    def list_faculty(self):
        return self.db.query("SELECT * FROM faculty ORDER BY faculty_id")

    def add_subject(self, subject_name, department="", faculty_id=None):
        if not subject_name.strip():
            raise ValidationError("Subject name cannot be empty.")
        if self.db.query("SELECT 1 FROM subjects WHERE subject_name=?", (subject_name.strip(),)):
            raise DuplicateRecordError("This subject already exists.")
        cur = self.db.execute("INSERT INTO subjects (subject_name, department, faculty_id) VALUES (?,?,?)",
                              (subject_name.strip(), department.strip(), faculty_id))
        return cur.lastrowid

    def list_subjects(self):
        return self.db.query("SELECT * FROM subjects ORDER BY subject_id")

    # ---------- attendance ----------
    def mark_attendance(self, student_id, subject_id, date, status):
        self.get_student(student_id)
        if not self.db.query("SELECT 1 FROM subjects WHERE subject_id=?", (subject_id,)):
            raise NotFoundError(f"Subject {subject_id} not found.")
        rec = AttendanceRecord(None, student_id, subject_id, date, status)   # validates date/status
        if self.db.query("SELECT 1 FROM attendance WHERE student_id=? AND subject_id=? AND date=?",
                         (student_id, subject_id, rec.date)):
            raise DuplicateRecordError(f"Attendance for student {student_id} on {rec.date} already exists.")
        cur = self.db.execute("INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?,?,?,?)",
                              (student_id, subject_id, rec.date, rec.status))
        rec.record_id = cur.lastrowid
        return rec

    def update_attendance(self, student_id, subject_id, date, status):
        rec = AttendanceRecord(None, student_id, subject_id, date, status)
        cur = self.db.execute("UPDATE attendance SET status=? WHERE student_id=? AND subject_id=? AND date=?",
                              (rec.status, student_id, subject_id, rec.date))
        if cur.rowcount == 0:
            raise NotFoundError("No attendance record found to update.")

    def attendance_exists(self, student_id, subject_id, date):
        return bool(self.db.query("SELECT 1 FROM attendance WHERE student_id=? AND subject_id=? AND date=?",
                                  (student_id, subject_id, validate_date(date))))

    def records_for_date(self, subject_id, date):
        return self.db.query("SELECT student_id, status FROM attendance WHERE subject_id=? AND date=?",
                             (subject_id, validate_date(date)))

    # ---------- calculations and reports ----------
    @staticmethod
    def calculate_percentage(attended, total):
        return round(attended * 100.0 / total, 2) if total else 0.0

    def student_report(self, student_id):
        """Subject-wise rows: (subject, total, attended, absent, percent)."""
        self.get_student(student_id)
        rows = self.db.query(
            "SELECT s.subject_name, COUNT(a.record_id) AS total, "
            "COALESCE(SUM(a.status='Present'),0) AS attended "
            "FROM subjects s JOIN attendance a ON a.subject_id=s.subject_id "
            "WHERE a.student_id=? GROUP BY s.subject_id ORDER BY s.subject_name", (student_id,))
        return [(r["subject_name"], r["total"], r["attended"], r["total"] - r["attended"],
                 self.calculate_percentage(r["attended"], r["total"])) for r in rows]

    def overall_percentage(self, student_id):
        r = self.db.query("SELECT COUNT(*) AS t, COALESCE(SUM(status='Present'),0) AS p "
                          "FROM attendance WHERE student_id=?", (student_id,))[0]
        return self.calculate_percentage(r["p"], r["t"])

    def subject_report(self):
        """Class-level rows per subject: (subject, total records, attended, percent)."""
        rows = self.db.query(
            "SELECT s.subject_name, COUNT(a.record_id) AS total, COALESCE(SUM(a.status='Present'),0) AS attended "
            "FROM subjects s LEFT JOIN attendance a ON a.subject_id=s.subject_id "
            "GROUP BY s.subject_id ORDER BY s.subject_name")
        return [(r["subject_name"], r["total"], r["attended"],
                 self.calculate_percentage(r["attended"], r["total"])) for r in rows]

    def class_report(self):
        """Rows per student: (id, name, total, attended, percent)."""
        rows = self.db.query(
            "SELECT st.student_id, st.name, COUNT(a.record_id) AS total, COALESCE(SUM(a.status='Present'),0) AS attended "
            "FROM students st LEFT JOIN attendance a ON a.student_id=st.student_id "
            "GROUP BY st.student_id ORDER BY st.student_id")
        return [(r["student_id"], r["name"], r["total"], r["attended"],
                 self.calculate_percentage(r["attended"], r["total"])) for r in rows]

    def find_low_attendance(self, limit=LOW_ATTENDANCE_LIMIT):
        return [row for row in self.class_report() if row[2] > 0 and row[4] < limit]

    def close(self):
        self.db.close()
