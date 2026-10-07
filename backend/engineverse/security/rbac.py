"""Role based access control (spec §71, §72).

Capabilities are checked server-side only. A client can render whatever it
likes; the API decides.
"""
from __future__ import annotations

ROLE_STUDENT = "student"
ROLE_MENTOR = "mentor"
ROLE_MODERATOR = "moderator"
ROLE_SUBJECT_EXPERT = "subject_expert"
ROLE_PROJECT_REVIEWER = "project_reviewer"
ROLE_ANALYTICS_ADMIN = "analytics_admin"
ROLE_CONTENT_ADMIN = "content_admin"
ROLE_SUPER_ADMIN = "super_admin"

ROLES = (
    ROLE_STUDENT,
    ROLE_MENTOR,
    ROLE_MODERATOR,
    ROLE_SUBJECT_EXPERT,
    ROLE_PROJECT_REVIEWER,
    ROLE_ANALYTICS_ADMIN,
    ROLE_CONTENT_ADMIN,
    ROLE_SUPER_ADMIN,
)

CAPABILITIES = (
    "content.create", "content.update", "content.publish", "content.delete",
    "users.manage", "users.roles", "community.moderate", "projects.review",
    "analytics.view", "settings.manage",
)

ROLE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    ROLE_STUDENT: (),
    ROLE_MENTOR: ("content.create", "community.moderate"),
    ROLE_MODERATOR: ("community.moderate", "content.update"),
    ROLE_SUBJECT_EXPERT: ("content.create", "content.update", "content.publish"),
    ROLE_PROJECT_REVIEWER: ("content.create", "content.update", "projects.review"),
    ROLE_ANALYTICS_ADMIN: ("analytics.view",),
    ROLE_CONTENT_ADMIN: (
        "content.create", "content.update", "content.publish",
        "content.delete", "community.moderate", "projects.review",
    ),
    ROLE_SUPER_ADMIN: CAPABILITIES,
}

ROLE_LABELS = {
    ROLE_STUDENT: "Student",
    ROLE_MENTOR: "Mentor",
    ROLE_MODERATOR: "Community Moderator",
    ROLE_SUBJECT_EXPERT: "Subject Expert",
    ROLE_PROJECT_REVIEWER: "Project Reviewer",
    ROLE_ANALYTICS_ADMIN: "Analytics Admin",
    ROLE_CONTENT_ADMIN: "Content Admin",
    ROLE_SUPER_ADMIN: "Super Admin",
}


class Forbidden(Exception):
    status_code = 403

    def __init__(self, message: str = "You do not have permission to do that.") -> None:
        super().__init__(message)
        self.message = message


def capabilities_for(role: str | None) -> tuple[str, ...]:
    if not role:
        return ()
    return ROLE_CAPABILITIES.get(role, ())


def can(role: str | None, capability: str) -> bool:
    return capability in capabilities_for(role)


def is_staff(role: str | None) -> bool:
    return bool(role) and role != ROLE_STUDENT


def assert_can(role: str | None, capability: str) -> None:
    if not can(role, capability):
        raise Forbidden()


def role_label(role: str | None) -> str:
    return ROLE_LABELS.get(role or "", "Student")
