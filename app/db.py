from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

try:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()  # type: ignore[misc,assignment]

from app.config import get_settings

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def seed_db(session: Session) -> None:
    from sqlalchemy import select
    from app.domain.models import Customer, Employee, Product

    if session.scalar(select(Employee)):
        return  # DB already seeded

    mgr = Employee(name="System Admin (Manager)", role="manager", principals=["mgr-all"])
    sales = Employee(name="Alice Sales", role="sales", principals=["sales-region-1"])
    session.add_all([mgr, sales])
    session.commit()

    cust = Customer(name="Acme Corp", email="enc:v1:acme@example.com", phone="555-0199", segment="enterprise", owner_employee_id=sales.id)
    prod1 = Product(sku="AX-SENSOR-01", name="3D Fleet Telemetry Sensor", unit_price=450.0, stock_qty=50)
    prod2 = Product(sku="AX-ROUTER-02", name="Governed AI Edge Gateway", unit_price=1200.0, stock_qty=20)
    session.add_all([cust, prod1, prod2])
    session.commit()


def init_db() -> None:
    from app.domain import models  # noqa: F401 — register mappers

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_db(session)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
