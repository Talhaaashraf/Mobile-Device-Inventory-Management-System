from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.api.deps import AdminUser, CurrentUser, DbSession, ManagerOrAdmin
from app.core.config import os_freshness_category
from app.models.assignment import AssignmentHistory
from app.models.device import Device
from app.models.enums import AuditStatus, DeviceStatus, DeviceType, OsType
from app.models.user import User
from app.schemas.device import (
    AssignmentHistoryRead,
    DashboardSummary,
    DeviceCreate,
    DeviceRead,
    DeviceUpdate,
    ImportResult,
    InStockDeviceItem,
    InStockSummary,
    LatestModelItem,
)
from app.services.csv_import import import_devices_from_csv

router = APIRouter(tags=["devices"])


def _get_device_or_404(db, device_id: UUID) -> Device:
    device = db.scalar(
        select(Device)
        .options(joinedload(Device.assigned_user))
        .where(Device.id == device_id)
    )
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def _validate_assigned_user(db, user_id: UUID | None) -> None:
    if user_id is None:
        return
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found or inactive")


def _apply_cellular_rules(is_cellular: bool, imei: str | None) -> None:
    if is_cellular and not imei:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="imei_number is required when is_cellular is true",
        )
    if not is_cellular and imei:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="imei_number must be empty when is_cellular is false",
        )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: DbSession, _: CurrentUser) -> DashboardSummary:
    total = db.scalar(select(func.count()).select_from(Device)) or 0
    unassigned = (
        db.scalar(select(func.count()).select_from(Device).where(Device.assigned_user_id.is_(None))) or 0
    )
 
    by_status = {s.value: 0 for s in DeviceStatus}
    for status_val, count in db.execute(
        select(Device.status, func.count()).group_by(Device.status)
    ).all():
        by_status[status_val.value] = count
 
    by_audit_status = {s.value: 0 for s in AuditStatus}
    for audit_val, count in db.execute(
        select(Device.audit_status, func.count()).group_by(Device.audit_status)
    ).all():
        by_audit_status[audit_val.value] = count
 
    by_os = {o.value: 0 for o in OsType}
    for os_val, count in db.execute(select(Device.os_type, func.count()).group_by(Device.os_type)).all():
        by_os[os_val.value] = count
 
    by_type = {t.value: 0 for t in DeviceType}
    for type_val, count in db.execute(
        select(Device.device_type, func.count()).group_by(Device.device_type)
    ).all():
        by_type[type_val.value] = count
 
    by_category = {
        "iPhone": 0,
        "iPad": 0,
        "Android Phone": 0,
        "Android Tablet": 0,
        "Smartwatch": 0,
    }
    for device_type, os_type, count in db.execute(
        select(Device.device_type, Device.os_type, func.count()).group_by(Device.device_type, Device.os_type)
    ).all():
        if os_type in (OsType.watchos, OsType.wear_os):
            by_category["Smartwatch"] += count
        elif device_type == DeviceType.phone and os_type == OsType.ios:
            by_category["iPhone"] += count
        elif device_type == DeviceType.tablet_ipad and os_type == OsType.ios:
            by_category["iPad"] += count
        elif device_type == DeviceType.phone and os_type == OsType.android:
            by_category["Android Phone"] += count
        elif device_type == DeviceType.tablet_android and os_type == OsType.android:
            by_category["Android Tablet"] += count
 
    freshness_groups = ["Latest", "Recent", "Outdated", "Unknown"]
    by_os_freshness = {o.value: {group: 0 for group in freshness_groups} for o in OsType}
    for os_type, os_version in db.execute(select(Device.os_type, Device.os_version)).all():
        group = os_freshness_category(os_type.value, os_version)
        if group not in by_os_freshness[os_type.value]:
            group = "Unknown"
        by_os_freshness[os_type.value][group] += 1
 
    by_project: dict[str, int] = {}
    for project_name, count in db.execute(select(Device.project_name, func.count()).group_by(Device.project_name)).all():
        key = project_name or "Unassigned Project"
        by_project[key] = count
 
    latest_models = [
        LatestModelItem(
            id=device.id,
            device_name=device.device_name,
            device_nickname=device.device_nickname,
            os_type=device.os_type,
            issued_to=device.issued_to,
        )
        for device in db.scalars(
            select(Device).where(Device.is_latest_model.is_(True)).order_by(Device.created_at.desc())
        ).all()
    ]
 
    in_stock_devices = [
        InStockDeviceItem(
            id=device.id,
            device_name=device.device_name,
            device_type=device.device_type,
            os_type=device.os_type,
            serial_number=device.serial_number,
        )
        for device in db.scalars(
            select(Device)
            .where(
                or_(Device.issued_to.is_(None), Device.issued_to == ""),
                Device.status == DeviceStatus.active,
            )
            .order_by(Device.device_name.asc())
        ).all()
    ]
 
    return DashboardSummary(
        total_devices=total,
        unassigned_devices=unassigned,
        by_status=by_status,
        by_os=by_os,
        by_type=by_type,
        by_category=by_category,
        by_os_freshness=by_os_freshness,
        by_project=by_project,
        by_audit_status=by_audit_status,
        latest_models=latest_models,
        in_stock=InStockSummary(count=len(in_stock_devices), list=in_stock_devices),
    )


@router.get("/devices", response_model=list[DeviceRead])
def list_devices(
    db: DbSession,
    _: CurrentUser,
    device_type: DeviceType | None = None,
    os_type: OsType | None = None,
    company: str | None = None,
    assigned_user_id: UUID | None = None,
    unassigned: bool | None = None,
    status_filter: DeviceStatus | None = Query(default=None, alias="status"),
    q: str | None = None,
) -> list[Device]:
    stmt = select(Device).options(joinedload(Device.assigned_user)).order_by(Device.created_at.desc())
    if device_type:
        stmt = stmt.where(Device.device_type == device_type)
    if os_type:
        stmt = stmt.where(Device.os_type == os_type)
    if company:
        stmt = stmt.where(Device.company.ilike(f"%{company}%"))
    if assigned_user_id:
        stmt = stmt.where(Device.assigned_user_id == assigned_user_id)
    if unassigned is True:
        stmt = stmt.where(Device.assigned_user_id.is_(None))
    if status_filter:
        stmt = stmt.where(Device.status == status_filter)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Device.device_name.ilike(like),
                Device.device_nickname.ilike(like),
                Device.serial_number.ilike(like),
                Device.imei_number.ilike(like),
            )
        )
    return list(db.scalars(stmt).unique().all())


@router.post("/devices", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: DbSession, current_user: ManagerOrAdmin) -> Device:
    _validate_assigned_user(db, payload.assigned_user_id)
    device = Device(**payload.model_dump())
    db.add(device)
    db.flush()
    if payload.assigned_user_id is not None:
        db.add(
            AssignmentHistory(
                device_id=device.id,
                from_user_id=None,
                to_user_id=payload.assigned_user_id,
                changed_by=current_user.id,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with duplicate serial, MAC, or IMEI already exists",
        )
    return _get_device_or_404(db, device.id)


@router.post("/devices/import", response_model=ImportResult)
async def import_devices_csv(
    db: DbSession,
    current_user: ManagerOrAdmin,
    file: UploadFile = File(...),
) -> ImportResult:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a .csv file")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")
    try:
        result = import_devices_from_csv(db, content, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ImportResult(**result)


@router.get("/devices/{device_id}", response_model=DeviceRead)
def get_device(device_id: UUID, db: DbSession, _: CurrentUser) -> Device:
    return _get_device_or_404(db, device_id)


@router.patch("/devices/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: UUID, payload: DeviceUpdate, db: DbSession, current_user: ManagerOrAdmin
) -> Device:
    device = _get_device_or_404(db, device_id)
    data = payload.model_dump(exclude_unset=True)
    clear_assigned = data.pop("clear_assigned_user", False)
    clear_imei = data.pop("clear_imei", False)
    clear_purchase = data.pop("clear_purchase_date", False)
    clear_return = data.pop("clear_date_of_return", False)

    if clear_assigned:
        data["assigned_user_id"] = None
    if clear_imei:
        data["imei_number"] = None
    if clear_purchase:
        data["purchase_date"] = None
    if clear_return:
        data["date_of_return"] = None

    if "assigned_user_id" in data:
        _validate_assigned_user(db, data["assigned_user_id"])

    old_assignee = device.assigned_user_id
    old_issued_to = device.issued_to
    new_is_cellular = data.get("is_cellular", device.is_cellular)
    new_imei = data.get("imei_number", device.imei_number)
    if clear_imei:
        new_imei = None
    _apply_cellular_rules(new_is_cellular, new_imei)

    for key, value in data.items():
        setattr(device, key, value)

    if "assigned_user_id" in data and data["assigned_user_id"] != old_assignee:
        db.add(
            AssignmentHistory(
                device_id=device.id,
                from_user_id=old_assignee,
                to_user_id=data["assigned_user_id"],
                changed_by=current_user.id,
            )
        )

    if "issued_to" in data and data["issued_to"] != old_issued_to:
        db.add(
            AssignmentHistory(
                device_id=device.id,
                from_user_id=old_assignee,
                to_user_id=device.assigned_user_id,
                changed_by=current_user.id,
                from_issued_to=old_issued_to,
                to_issued_to=data["issued_to"],
                project_name=device.project_name,
                project_manager=device.project_manager,
                division=device.division,
                resident_location=device.resident_location,
                audit_status=device.audit_status,
                date_of_return=device.date_of_return,
                notes=device.notes,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with duplicate serial, MAC, or IMEI already exists",
        )
    return _get_device_or_404(db, device.id)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: UUID, db: DbSession, _: AdminUser) -> None:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    db.delete(device)
    db.commit()


@router.get("/devices/{device_id}/history", response_model=list[AssignmentHistoryRead])
def device_history(device_id: UUID, db: DbSession, _: CurrentUser) -> list[AssignmentHistory]:
    if db.get(Device, device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    stmt = (
        select(AssignmentHistory)
        .options(
            joinedload(AssignmentHistory.from_user),
            joinedload(AssignmentHistory.to_user),
            joinedload(AssignmentHistory.changed_by_user),
        )
        .where(AssignmentHistory.device_id == device_id)
        .order_by(AssignmentHistory.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())
