"""User roles. User is abstract; Admin, Faculty and StudentUser inherit from it."""
from abc import ABC, abstractmethod

from database import hash_password


class User(ABC):
    def __init__(self, username, password_hash, ref_id=None):
        self.username = username
        self.__password_hash = password_hash   # encapsulated
        self.ref_id = ref_id                   # faculty_id / student_id

    def check_password(self, password) -> bool:
        return self.__password_hash == hash_password(password)

    @abstractmethod
    def get_role(self) -> str:
        """Name of the role."""

    @abstractmethod
    def menu_options(self) -> list:
        """Screens this role may open (polymorphism)."""

    def __str__(self):
        return f"{self.username} ({self.get_role()})"


class Admin(User):
    def get_role(self):
        return "Admin"

    def menu_options(self):
        return ["Students", "Faculty & Subjects", "Reports"]


class Faculty(User):
    def get_role(self):
        return "Faculty"

    def menu_options(self):
        return ["Mark Attendance", "Reports"]


class StudentUser(User):
    def get_role(self):
        return "Student"

    def menu_options(self):
        return ["My Attendance"]


ROLE_CLASSES = {"Admin": Admin, "Faculty": Faculty, "Student": StudentUser}
