"""RBAC role slugs and permission catalog for AICTE SecureDC."""

SUPER_ADMIN = "super_admin"
SECURITY_ADMIN = "security_admin"
NETWORK_ADMIN = "network_admin"
SERVER_ADMIN = "server_admin"
AUDITOR = "auditor"

SYSTEM_ROLES = (
    (SUPER_ADMIN, "Super Admin", "Full platform control"),
    (SECURITY_ADMIN, "Security Admin", "User security and access oversight"),
    (NETWORK_ADMIN, "Network Admin", "Firewall inventory and rule change requests"),
    (SERVER_ADMIN, "Server Admin", "Server inventory and operations"),
    (AUDITOR, "Auditor", "Read-only access for compliance review"),
)

PERMISSIONS = (
    ("user", "create", "Create users"),
    ("user", "read", "View users"),
    ("user", "update", "Update users"),
    ("user", "disable", "Disable users"),
    ("role", "create", "Create roles"),
    ("role", "read", "View roles"),
    ("role", "update", "Update roles"),
    ("role", "assign", "Assign roles to users"),
    ("permission", "create", "Create permissions"),
    ("permission", "read", "View permissions"),
    ("permission", "update", "Update permission assignments on roles"),
    ("dashboard", "read", "View cybersecurity dashboard"),
    ("server", "read", "View servers"),
    ("server", "create", "Add servers"),
    ("server", "update", "Edit servers"),
    ("server", "delete", "Delete servers"),
    ("firewall", "read", "View firewalls, rules, and approval history"),
    ("firewall", "create", "Add firewall devices"),
    ("firewall", "update", "Edit firewall devices"),
    ("firewall", "request", "Request firewall rule changes"),
    ("firewall", "approve", "Approve firewall rule changes"),
    ("firewall", "reject", "Reject firewall rule changes"),
    ("audit", "read", "View security audit logs"),
    ("audit", "verify", "Run blockchain integrity checks"),
    ("audit", "alert", "Acknowledge integrity security alerts"),
    ("alert", "read", "View alerts"),
)

ROLE_PERMISSIONS = {
    SUPER_ADMIN: "*",
    SECURITY_ADMIN: (
        "user:read",
        "user:update",
        "user:disable",
        "role:read",
        "role:assign",
        "permission:read",
        "dashboard:read",
        "alert:read",
        "server:read",
        "firewall:read",
        "firewall:approve",
        "firewall:reject",
        "audit:read",
        "audit:verify",
        "audit:alert",
    ),
    NETWORK_ADMIN: (
        "dashboard:read",
        "firewall:read",
        "firewall:create",
        "firewall:update",
        "firewall:request",
        "alert:read",
    ),
    SERVER_ADMIN: (
        "dashboard:read",
        "server:read",
        "server:create",
        "server:update",
        "server:delete",
        "alert:read",
    ),
    AUDITOR: (
        "user:read",
        "role:read",
        "permission:read",
        "dashboard:read",
        "server:read",
        "firewall:read",
        "alert:read",
        "audit:read",
        "audit:verify",
    ),
}
