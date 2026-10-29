"""Unit tests - run with:  python -m unittest tests -v"""
import unittest

from manager import AttendanceManager
from models import (AuthenticationError, DuplicateRecordError, NotFoundError, ValidationError, Student)
from user import Admin, Faculty, StudentUser, User


class AttendanceTests(unittest.TestCase):
    def setUp(self):
        self.m = AttendanceManager(":memory:")
        self.sid, self.stu_login = self.m.add_student("Asha Rao", "CSE", 3, "9999999999")
        self.sub = self.m.add_subject("Python", "CSE")

    def tearDown(self):
        self.m.close()

    # TC-01 login
    def test_login_wrong_password(self):
        with self.assertRaises(AuthenticationError):
            self.m.authenticate("admin", "wrong")

    def test_login_roles(self):
        self.assertIsInstance(self.m.authenticate("admin", "admin123"), Admin)
        self.assertIsInstance(self.m.authenticate(self.stu_login, self.stu_login), StudentUser)
        _, fac_login = self.m.add_faculty("Dr. Rao", "CSE")
        self.assertIsInstance(self.m.authenticate(fac_login, fac_login), Faculty)

    # TC-02 duplicate
    def test_duplicate_attendance_rejected(self):
        self.m.mark_attendance(self.sid, self.sub, "2026-09-01", "Present")
        with self.assertRaises(DuplicateRecordError):
            self.m.mark_attendance(self.sid, self.sub, "2026-09-01", "Absent")

    def test_update_attendance(self):
        self.m.mark_attendance(self.sid, self.sub, "2026-09-01", "Absent")
        self.m.update_attendance(self.sid, self.sub, "2026-09-01", "Present")
        self.assertEqual(self.m.student_report(self.sid)[0][2], 1)

    # TC-03 percentage
    def test_percentage(self):
        for d in range(1, 25):
            self.m.mark_attendance(self.sid, self.sub, f"2026-09-{d:02d}", "Present" if d <= 18 else "Absent")
        self.assertEqual(self.m.student_report(self.sid)[0][4], 75.0)
        self.assertEqual(self.m.overall_percentage(self.sid), 75.0)
        self.assertEqual(AttendanceManager.calculate_percentage(0, 0), 0.0)

    # TC-04 low attendance
    def test_low_attendance(self):
        for d in range(1, 11):
            self.m.mark_attendance(self.sid, self.sub, f"2026-09-{d:02d}", "Present" if d <= 7 else "Absent")
        low = self.m.find_low_attendance(75)
        self.assertEqual([r[0] for r in low], [self.sid])
        self.assertEqual(low[0][4], 70.0)

    # validation
    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            self.m.add_student("", "CSE", 3)
        with self.assertRaises(ValidationError):
            self.m.add_student("Ravi", "CSE", 20)
        with self.assertRaises(ValidationError):
            self.m.mark_attendance(self.sid, self.sub, "01-09-2026", "Present")
        with self.assertRaises(ValidationError):
            self.m.mark_attendance(self.sid, self.sub, "2026-09-01", "Late")
        with self.assertRaises(NotFoundError):
            self.m.mark_attendance(999, self.sub, "2026-09-01", "Present")

    def test_student_crud_and_search(self):
        self.m.update_student(self.sid, "Asha R", "ECE", 4)
        self.assertEqual(self.m.get_student(self.sid).department, "ECE")
        self.assertEqual(len(self.m.list_students("asha")), 1)
        self.m.delete_student(self.sid)
        self.assertEqual(self.m.list_students(), [])
        with self.assertRaises(AuthenticationError):
            self.m.authenticate(self.stu_login, self.stu_login)

    def test_encapsulation_and_abstraction(self):
        s = Student(1, "A", "CSE", 1)
        with self.assertRaises(AttributeError):
            s.student_id = 5            # read-only property
        with self.assertRaises(TypeError):
            User("x", "y")              # abstract class cannot be instantiated

    def test_class_and_subject_reports(self):
        self.m.mark_attendance(self.sid, self.sub, "2026-09-01", "Present")
        self.assertEqual(self.m.class_report()[0][4], 100.0)
        self.assertEqual(self.m.subject_report()[0][2], 1)


if __name__ == "__main__":
    unittest.main()
