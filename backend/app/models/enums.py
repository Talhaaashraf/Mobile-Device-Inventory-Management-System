import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class DeviceType(str, enum.Enum):
    phone = "phone"
    tablet_ipad = "tablet_ipad"
    tablet_android = "tablet_android"
    smartwatch = "smartwatch"


class OsType(str, enum.Enum):
    ios = "ios"
    android = "android"
    watchos = "watchos"
    wear_os = "wear_os"


class DeviceStatus(str, enum.Enum):
    active = "active"
    in_repair = "in_repair"
    retired = "retired"
    lost = "lost"
