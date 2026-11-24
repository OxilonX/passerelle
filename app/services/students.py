from datetime import date
from typing import Callable, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, delete, col

from app.database import get_session
from app.models import Student, Internship


class StudentService:
    def __init__(self, session_factory: Callable[[], Session] = get_session) -> None:
        self._session_factory = session_factory

    def add_student(
        self,
        registration_number: str,
        last_name: str,
        first_name: str,
        date_of_birth: date,
        address: str,
        email: str,
    ) -> Student:
        reg_clean = registration_number.strip()
        last_clean = last_name.strip()
        first_clean = first_name.strip()
        address_clean = address.strip()
        email_clean = email.strip()

        if not reg_clean:
            raise ValueError("Registration number is required.")
        if not last_clean or not first_clean:
            raise ValueError("Last name and first name are required.")
        if not address_clean or not email_clean:
            raise ValueError("Address and email are required.")

        with self._session_factory() as session:
            existing = session.exec(
                select(Student).where(Student.registration_number == reg_clean)
            ).first()
            if existing is not None:
                raise ValueError(
                    f"A student with registration number '{reg_clean}' already exists."
                )

            student = Student(
                registration_number=reg_clean,
                last_name=last_clean,
                first_name=first_clean,
                date_of_birth=date_of_birth,
                address=address_clean,
                email=email_clean,
            )
            session.add(student)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError(
                    f"Registration number '{reg_clean}' is already in use."
                ) from exc
            session.refresh(student)
            return student

    def find_student(self, registration_number: str) -> Optional[Student]:
        reg_clean = registration_number.strip()
        if not reg_clean:
            return None

        with self._session_factory() as session:
            selected_student = select(Student).where(
                Student.registration_number == reg_clean
            )
            return session.exec(selected_student).first()

    def update_student(
        self,
        registration_number: str,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        new_registration_number: Optional[str] = None,
    ) -> Student:
        reg_clean = registration_number.strip()
        if not reg_clean:
            raise ValueError("Registration number is required.")

        with self._session_factory() as session:
            student = session.exec(
                select(Student).where(Student.registration_number == reg_clean)
            ).first()
            if student is None:
                raise ValueError(
                    f"No student found with registration number '{reg_clean}'."
                )

            if new_registration_number is not None:
                new_reg_clean = new_registration_number.strip()
                if not new_reg_clean:
                    raise ValueError("New registration number cannot be empty.")
                if new_reg_clean != student.registration_number:
                    duplicate = session.exec(
                        select(Student).where(
                            Student.registration_number == new_reg_clean
                        )
                    ).first()
                    if duplicate is not None:
                        raise ValueError(
                            f"Registration number '{new_reg_clean}' is already in use."
                        )
                    student.registration_number = new_reg_clean

            if last_name is not None:
                last_clean = last_name.strip()
                if not last_clean:
                    raise ValueError("Last name cannot be empty.")
                student.last_name = last_clean

            if first_name is not None:
                first_clean = first_name.strip()
                if not first_clean:
                    raise ValueError("First name cannot be empty.")
                student.first_name = first_clean

            if date_of_birth is not None:
                student.date_of_birth = date_of_birth

            if address is not None:
                address_clean = address.strip()
                if not address_clean:
                    raise ValueError("Address cannot be empty.")
                student.address = address_clean

            if email is not None:
                email_clean = email.strip()
                if not email_clean:
                    raise ValueError("Email cannot be empty.")
                student.email = email_clean

            session.add(student)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError(
                    "Failed to update student due to a uniqueness constraint."
                ) from exc
            session.refresh(student)
            return student

    def delete_student(self, registration_number: str) -> bool:
        reg_clean = registration_number.strip()
        if not reg_clean:
            raise ValueError("Registration number is required.")

        with self._session_factory() as session:
            student = session.exec(
                select(Student).where(Student.registration_number == reg_clean)
            ).first()
            if student is None:
                return False

            if student.id is None:
                return False
            session.exec(
                delete(Internship).where(col(Internship.student_id) == student.id)
            )
            session.delete(student)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError(
                    "Failed to delete student and related records."
                ) from exc
            return True


student_service = StudentService()
