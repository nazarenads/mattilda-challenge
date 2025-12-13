"""
Seed script to populate the database with test data.

Run inside the Docker container:
    docker compose run --rm app python -m scripts.seed_data
"""

from datetime import datetime, timedelta
import random

from sqlalchemy.orm import Session

from app.db.database import Base, engine, SessionLocal
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


def clear_database(db: Session) -> None:
    """Clear all existing data."""
    db.query(PaymentAllocation).delete()
    db.query(Payment).delete()
    db.query(Invoice).delete()
    db.query(Student).delete()
    db.query(School).delete()
    db.commit()
    print("✓ Cleared existing data")


def create_schools(db: Session) -> list[School]:
    """Create sample schools."""
    schools_data = [
        {"name": "Colegio Guadalupe", "country": "MX", "tax_id": "XAXX010101000"},
        {"name": "Instituto Tecnológico de Monterrey", "country": "MX", "tax_id": "ITM850101ABC"},
        {"name": "Colegio Simón Bolívar", "country": "CO", "tax_id": "900123456-1"},
        {"name": "Gimnasio Moderno", "country": "CO", "tax_id": "860012345-7"},
        {"name": "Colegio Bilingüe de Bogotá", "country": "CO", "tax_id": "830045678-2"},
    ]

    schools = []
    now = datetime.now()
    for data in schools_data:
        school = School(
            name=data["name"],
            country=data["country"],
            tax_id=data["tax_id"],
            created_at=now,
            updated_at=now,
        )
        db.add(school)
        schools.append(school)

    db.commit()
    for school in schools:
        db.refresh(school)

    print(f"✓ Created {len(schools)} schools")
    return schools


def create_students(db: Session, schools: list[School]) -> list[Student]:
    """Create sample students for each school."""
    first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Lucas", "Sophia", "Mason", "Isabella", "James"]
    last_names = ["Smith", "García", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Rodríguez", "Martínez"]

    students = []
    now = datetime.now()
    student_counter = 1

    for school in schools:
        num_students = random.randint(8, 15)
        for i in range(num_students):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            student = Student(
                identifier=f"{school.country}-{school.id:03d}-{i+1:04d}",
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}.{student_counter}@example.com",
                school_id=school.id,
                created_at=now,
                updated_at=now,
            )
            db.add(student)
            students.append(student)
            student_counter += 1

    db.commit()
    for student in students:
        db.refresh(student)

    print(f"✓ Created {len(students)} students")
    return students


def create_invoices(db: Session, students: list[Student]) -> list[Invoice]:
    """Create sample invoices for students."""
    invoices = []
    now = datetime.now()

    invoice_descriptions = [
        "Monthly tuition fee",
        "Registration fee",
        "Laboratory materials",
        "Field trip - Museum visit",
        "Sports equipment",
        "Library annual fee",
        "Exam fees",
        "Graduation ceremony",
    ]

    currencies_by_country = {
        "MX": "MXN",
        "CO": "COP",
    }

    statuses = [
        InvoiceStatus.PENDING.value,
        InvoiceStatus.PENDING.value,
        InvoiceStatus.PAID.value,
        InvoiceStatus.OVERDUE.value,
        InvoiceStatus.PARTIALLY_PAID.value,
        InvoiceStatus.DRAFT.value,
    ]

    invoice_counter = 1
    for student in students:
        school = db.query(School).filter(School.id == student.school_id).first()
        currency = currencies_by_country.get(school.country, "USD")

        num_invoices = random.randint(1, 4)
        for _ in range(num_invoices):
            days_ago = random.randint(1, 180)
            issue_date = now - timedelta(days=days_ago)
            due_date = issue_date + timedelta(days=30)

            status = random.choice(statuses)
            if due_date < now and status == InvoiceStatus.PENDING.value:
                status = InvoiceStatus.OVERDUE.value

            amount = random.choice([5000, 10000, 15000, 25000, 50000, 75000, 100000])

            invoice = Invoice(
                invoice_number=f"INV-{now.year}-{invoice_counter:06d}",
                amount_in_cents=amount,
                currency=currency,
                status=status,
                issue_date=issue_date,
                due_date=due_date,
                description=random.choice(invoice_descriptions),
                student_id=student.id,
                created_at=issue_date,
                updated_at=now,
            )
            db.add(invoice)
            invoices.append(invoice)
            invoice_counter += 1

    db.commit()
    for invoice in invoices:
        db.refresh(invoice)

    print(f"✓ Created {len(invoices)} invoices")
    return invoices


def create_payments_and_allocations(db: Session, students: list[Student], invoices: list[Invoice]) -> None:
    """Create payments and allocate them to invoices."""
    now = datetime.now()
    payment_methods = [
        PaymentMethod.CASH.value,
        PaymentMethod.CARD.value,
        PaymentMethod.BANK_TRANSFER.value,
    ]

    payment_statuses = [
        PaymentStatus.COMPLETED.value,
        PaymentStatus.COMPLETED.value,
        PaymentStatus.COMPLETED.value,
        PaymentStatus.PENDING.value,
        PaymentStatus.FAILED.value,
    ]

    payments_created = 0
    allocations_created = 0

    paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID.value]
    for invoice in paid_invoices:
        payment = Payment(
            amount_in_cents=invoice.amount_in_cents,
            status=PaymentStatus.COMPLETED.value,
            payment_method=random.choice(payment_methods),
            student_id=invoice.student_id,
            created_at=invoice.due_date - timedelta(days=random.randint(1, 10)),
            updated_at=now,
        )
        db.add(payment)
        db.flush()

        allocation = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_in_cents=invoice.amount_in_cents,
            created_at=payment.created_at,
        )
        db.add(allocation)
        payments_created += 1
        allocations_created += 1

    partial_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PARTIALLY_PAID.value]
    for invoice in partial_invoices:
        partial_amount = invoice.amount_in_cents // random.randint(2, 4)
        payment = Payment(
            amount_in_cents=partial_amount,
            status=PaymentStatus.COMPLETED.value,
            payment_method=random.choice(payment_methods),
            student_id=invoice.student_id,
            created_at=invoice.issue_date + timedelta(days=random.randint(5, 20)),
            updated_at=now,
        )
        db.add(payment)
        db.flush()

        allocation = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_in_cents=partial_amount,
            created_at=payment.created_at,
        )
        db.add(allocation)
        payments_created += 1
        allocations_created += 1

    for student in random.sample(students, min(10, len(students))):
        payment = Payment(
            amount_in_cents=random.choice([5000, 10000, 20000]),
            status=random.choice(payment_statuses),
            payment_method=random.choice(payment_methods),
            student_id=student.id,
            created_at=now - timedelta(days=random.randint(1, 30)),
            updated_at=now,
        )
        db.add(payment)
        payments_created += 1

    db.commit()
    print(f"✓ Created {payments_created} payments")
    print(f"✓ Created {allocations_created} payment allocations")


def print_summary(db: Session) -> None:
    """Print a summary of the seeded data."""
    schools_count = db.query(School).count()
    students_count = db.query(Student).count()
    invoices_count = db.query(Invoice).count()
    payments_count = db.query(Payment).count()
    allocations_count = db.query(PaymentAllocation).count()

    print("\n" + "=" * 50)
    print("DATABASE SEED SUMMARY")
    print("=" * 50)
    print(f"Schools:             {schools_count}")
    print(f"Students:            {students_count}")
    print(f"Invoices:            {invoices_count}")
    print(f"Payments:            {payments_count}")
    print(f"Payment Allocations: {allocations_count}")
    print("=" * 50)

    print("\nInvoices by status:")
    for status in InvoiceStatus:
        count = db.query(Invoice).filter(Invoice.status == status.value).count()
        if count > 0:
            print(f"  {status.value:15} {count}")

    print("\nPayments by status:")
    for status in PaymentStatus:
        count = db.query(Payment).filter(Payment.status == status.value).count()
        if count > 0:
            print(f"  {status.value:15} {count}")

    print("\nPayments by method:")
    for method in PaymentMethod:
        count = db.query(Payment).filter(Payment.payment_method == method.value).count()
        if count > 0:
            print(f"  {method.value:15} {count}")


def main():
    print("\n🌱 Starting database seed...\n")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        clear_database(db)
        schools = create_schools(db)
        students = create_students(db, schools)
        invoices = create_invoices(db, students)
        create_payments_and_allocations(db, students, invoices)
        print_summary(db)
        print("\n✅ Database seeded successfully!\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
