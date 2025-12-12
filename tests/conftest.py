from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.db.database import Base
from app.db.models import (
    School,
    Student,
    Invoice,
    Payment,
    PaymentAllocation,
    InvoiceStatus,
    PaymentStatus,
    PaymentMethod,
)
from app.dependencies import get_db
from app.main import app


engine = create_engine(settings.database_url, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class DatabaseHelpers:
    """Helper class for creating test data directly in the database."""

    def __init__(self, db: Session):
        self.db = db

    def create_school(
        self,
        name: str = "Test School",
        country: str = "US",
        tax_id: str = "123456789",
    ) -> School:
        now = datetime.now()
        school = School(
            name=name,
            country=country,
            tax_id=tax_id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(school)
        self.db.commit()
        self.db.refresh(school)
        return school

    def create_student(
        self,
        school: School,
        identifier: str = "ID-001",
        name: str = "Test Student",
        email: str = "student@example.com",
    ) -> Student:
        now = datetime.now()
        student = Student(
            identifier=identifier,
            name=name,
            email=email,
            school_id=school.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def create_invoice(
        self,
        student: Student,
        invoice_number: str = "INV-001",
        amount_in_cents: int = 10000,
        currency: str = "USD",
        status: str = InvoiceStatus.PENDING.value,
        issue_date: datetime = None,
        due_date: datetime = None,
        description: str = None,
    ) -> Invoice:
        now = datetime.now()
        invoice = Invoice(
            invoice_number=invoice_number,
            amount_in_cents=amount_in_cents,
            currency=currency,
            status=status,
            issue_date=issue_date or now,
            due_date=due_date or now,
            description=description,
            student_id=student.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_payment(
        self,
        student: Student,
        amount_in_cents: int = 10000,
        status: str = PaymentStatus.COMPLETED.value,
        payment_method: str = PaymentMethod.CARD.value,
    ) -> Payment:
        now = datetime.now()
        payment = Payment(
            amount_in_cents=amount_in_cents,
            status=status,
            payment_method=payment_method,
            student_id=student.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def create_allocation(
        self,
        payment: Payment,
        invoice: Invoice,
        amount_in_cents: int = 5000,
    ) -> PaymentAllocation:
        now = datetime.now()
        allocation = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_in_cents=amount_in_cents,
            created_at=now,
        )
        self.db.add(allocation)
        self.db.commit()
        self.db.refresh(allocation)
        return allocation

    def get_school(self, school_id: int) -> School | None:
        return self.db.query(School).filter(School.id == school_id).first()

    def get_student(self, student_id: int) -> Student | None:
        return self.db.query(Student).filter(Student.id == student_id).first()

    def get_invoice(self, invoice_id: int) -> Invoice | None:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def get_payment(self, payment_id: int) -> Payment | None:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_allocation(self, allocation_id: int) -> PaymentAllocation | None:
        return self.db.query(PaymentAllocation).filter(PaymentAllocation.id == allocation_id).first()

    def count_schools(self) -> int:
        return self.db.query(School).count()

    def count_students(self) -> int:
        return self.db.query(Student).count()

    def count_invoices(self) -> int:
        return self.db.query(Invoice).count()

    def count_payments(self) -> int:
        return self.db.query(Payment).count()

    def count_allocations(self) -> int:
        return self.db.query(PaymentAllocation).count()


@pytest.fixture
def db_helpers(db_session) -> DatabaseHelpers:
    return DatabaseHelpers(db_session)
