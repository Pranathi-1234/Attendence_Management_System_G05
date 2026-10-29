"""Data classes and custom exceptions for the Attendance Management System."""
from datetime import datetime


class AttendanceError(Exception):
    """Base class for all application errors."""


class ValidationError(AttendanceError):
    """Raised when user input is invalid."""


class DuplicateRecordError(AttendanceError):
    """Raised when attendance is already recorded for that student/subject/date."""


class NotFoundError(AttendanceError):
    """Raised when a requested record does not exist."""


class AuthenticationError(AttendanceError):
    """Raised when the username or password is wrong."""


def validate_date(value: str) -> str:
    """Return the date in YYYY-MM-DD format or raise ValidationError."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        raise ValidationError("Date must be in YYYY-MM-DD format.")


class Student:
    """A student. The id is private (encapsulation) and read-only."""

    def __init__(self, student_id, name, department, semester, contact=""):
        self.__student_id = student_id
        self.name = name
        self.department = department
        self.semester = semester
        self.contact = contact

    @property
    def student_id(self):
        return self.__student_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        if not value or not str(value).strip():
            raise ValidationError("Student name cannot be empty.")
        self.__name = str(value).strip()

    @property
    def department(self):
        return self.__department

    @department.setter
    def department(self, value):
        if not value or not str(value).strip():
            raise ValidationError("Department cannot be empty.")
        self.__department = str(value).strip()

    @property
    def semester(self):
        return self.__semester

    @semester.setter
    def semester(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Semester must be a number.")
        if not 1 <= value <= 12:
            raise ValidationError("Semester must be between 1 and 12.")
        self.__semester = value

    def __str__(self):
        return f"{self.student_id} - {self.name} ({self.department}, Sem {self.semester})"


class AttendanceRecord:
    """One student's attendance for one subject on one date."""

    VALID_STATUS = ("Present", "Absent")

    def __init__(self, record_id, student_id, subject_id, date, status):
        self.record_id = record_id
        self.student_id = student_id
        self.subject_id = subject_id
        self.date = date
        self.status = status

    @property
    def date(self):
        return self.__date

    @date.setter
    def date(self, value):
        self.__date = validate_date(value)

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value):
        if value not in self.VALID_STATUS:
            raise ValidationError("Status must be 'Present' or 'Absent'.")
        self.__status = value

    def __str__(self):
        return f"{self.date}: student {self.student_id}, subject {self.subject_id} -> {self.status}"
