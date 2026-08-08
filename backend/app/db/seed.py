from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.device import Device
from app.models.enums import DeviceStatus, DeviceType, OsType, UserRole
from app.models.user import User


def seed_database(db: Session) -> None:
    existing = db.scalar(select(User).where(User.email == "admin@company.com"))
    if existing:
        return

    admin = User(
        full_name="System Admin",
        email="admin@company.com",
        password_hash=hash_password("Admin123!"),
        role=UserRole.admin,
        department="IT",
        is_active=True,
    )
    manager = User(
        full_name="Sara Manager",
        email="manager@company.com",
        password_hash=hash_password("Manager123!"),
        role=UserRole.manager,
        department="Operations",
        is_active=True,
    )
    viewer = User(
        full_name="View Only",
        email="viewer@company.com",
        password_hash=hash_password("Viewer123!"),
        role=UserRole.viewer,
        department="Finance",
        is_active=True,
    )
    db.add_all([admin, manager, viewer])
    db.flush()

    devices = [
        Device(
            device_name="iPhone 14 Pro",
            device_nickname="Ali's Work Phone",
            device_type=DeviceType.phone,
            os_type=OsType.ios,
            os_version="17.4.1",
            is_cellular=True,
            imei_number="356938035643809",
            serial_number="SN-IPHONE-001",
            mac_address="A1:B2:C3:D4:E5:F6",
            company="Acme Corp",
            assigned_user_id=manager.id,
            status=DeviceStatus.active,
            purchase_date=date(2024, 3, 15),
        ),
        Device(
            device_name="Samsung Galaxy S24",
            device_nickname="Ops Android Phone",
            device_type=DeviceType.phone,
            os_type=OsType.android,
            os_version="14",
            is_cellular=True,
            imei_number="490154203237518",
            serial_number="SN-GALAXY-002",
            mac_address="11:22:33:44:55:66",
            company="Acme Corp",
            assigned_user_id=None,
            status=DeviceStatus.active,
            purchase_date=date(2024, 6, 1),
        ),
        Device(
            device_name="iPad Pro 12.9",
            device_nickname="Design Wi-Fi iPad",
            device_type=DeviceType.tablet_ipad,
            os_type=OsType.ios,
            os_version="17.5",
            is_cellular=False,
            imei_number=None,
            serial_number="SN-IPAD-003",
            mac_address="AA:BB:CC:DD:EE:FF",
            company="Acme Design",
            assigned_user_id=viewer.id,
            status=DeviceStatus.active,
            purchase_date=date(2023, 11, 20),
        ),
        Device(
            device_name="Samsung Galaxy Tab S9",
            device_nickname="Field Tablet",
            device_type=DeviceType.tablet_android,
            os_type=OsType.android,
            os_version="14",
            is_cellular=True,
            imei_number="353918101234567",
            serial_number="SN-TAB-004",
            mac_address="01:23:45:67:89:AB",
            company="Acme Field",
            assigned_user_id=None,
            status=DeviceStatus.in_repair,
            purchase_date=date(2024, 1, 10),
        ),
        Device(
            device_name="Apple Watch Series 9",
            device_nickname="Admin Watch",
            device_type=DeviceType.smartwatch,
            os_type=OsType.watchos,
            os_version="10.3",
            is_cellular=False,
            imei_number=None,
            serial_number="SN-WATCH-005",
            mac_address="DE:AD:BE:EF:00:01",
            company="Acme Corp",
            assigned_user_id=admin.id,
            status=DeviceStatus.active,
            purchase_date=date(2024, 2, 2),
        ),
        Device(
            device_name="Google Pixel Watch 2",
            device_nickname="Retired Wear OS",
            device_type=DeviceType.smartwatch,
            os_type=OsType.wear_os,
            os_version="4.0",
            is_cellular=True,
            imei_number="359827104567890",
            serial_number="SN-WATCH-006",
            mac_address="CA:FE:BA:BE:12:34",
            company="Acme Legacy",
            assigned_user_id=None,
            status=DeviceStatus.retired,
            purchase_date=date(2022, 8, 8),
        ),
        Device(
            device_name="iPhone 12",
            device_nickname="Lost Device Case",
            device_type=DeviceType.phone,
            os_type=OsType.ios,
            os_version="16.7",
            is_cellular=True,
            imei_number="354281076543210",
            serial_number="SN-IPHONE-007",
            mac_address="AB:CD:EF:12:34:56",
            company="Acme Corp",
            assigned_user_id=None,
            status=DeviceStatus.lost,
            purchase_date=date(2021, 5, 5),
        ),
    ]
    db.add_all(devices)
    db.commit()
