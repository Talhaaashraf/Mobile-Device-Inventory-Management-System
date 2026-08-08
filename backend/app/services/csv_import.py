import csv
import io
from datetime import date, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import AssignmentHistory
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceCreate

REQUIRED_COLUMNS = {
    "device_name",
    "device_nickname",
    "device_type",
    "os_type",
    "os_version",
    "is_cellular",
    "serial_number",
    "mac_address",
    "company",
}


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid purchase_date '{value}' (use YYYY-MM-DD)")


def _resolve_assignee(db: Session, email: str | None):
    if not email:
        return None
    user = db.scalar(select(User).where(User.email == email.lower(), User.is_active.is_(True)))
    if user is None:
        raise ValueError(f"Assigned user email not found or inactive: {email}")
    return user.id


def _format_validation_error(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors())


def import_devices_from_csv(db: Session, content: bytes, changed_by_id) -> dict:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")

    headers = {h.strip().lower() for h in reader.fieldnames if h}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    created = 0
    errors: list[dict] = []

    for index, raw in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not any(row.values()):
            continue

        try:
            with db.begin_nested():
                is_cellular = _truthy(row.get("is_cellular", ""))
                imei = row.get("imei_number") or None
                if not is_cellular:
                    imei = None

                assigned_user_id = _resolve_assignee(db, row.get("assigned_user_email") or None)
                payload = DeviceCreate(
                    device_name=row["device_name"],
                    device_nickname=row["device_nickname"],
                    device_type=row["device_type"].lower(),
                    os_type=row["os_type"].lower(),
                    os_version=row["os_version"],
                    is_cellular=is_cellular,
                    imei_number=imei,
                    serial_number=row["serial_number"],
                    mac_address=row["mac_address"],
                    company=row["company"],
                    assigned_user_id=assigned_user_id,
                    status=(row.get("status") or "active").lower(),
                    purchase_date=_parse_date(row.get("purchase_date", "")),
                )

                device = Device(**payload.model_dump())
                db.add(device)
                db.flush()

                if assigned_user_id is not None:
                    db.add(
                        AssignmentHistory(
                            device_id=device.id,
                            from_user_id=None,
                            to_user_id=assigned_user_id,
                            changed_by=changed_by_id,
                        )
                    )
            created += 1
        except ValidationError as exc:
            errors.append({"row": index, "error": _format_validation_error(exc)})
        except (ValueError, KeyError, IntegrityError) as exc:
            errors.append({"row": index, "error": str(exc.orig if isinstance(exc, IntegrityError) else exc)})

    db.commit()
    return {"created": created, "failed": len(errors), "errors": errors}
