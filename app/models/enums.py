from enum import Enum

class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN",
    ADMIN = "ADMIN",
    MANAGER = "MANAGER",
    STAFF = "STAFF",
    USER = "USER",
    GUEST = "GUEST"

class AuthProvider(str, Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"
    APPLE = "APPLE"

class UserStatus(str, Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION",
    ACTIVE = "ACTIVE",
    INACTIVE = "INACTIVE",
    SUSPENDED = "SUSPENDED",
    BANNED = "BANNED"

