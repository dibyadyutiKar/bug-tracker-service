"""Enum definitions for models."""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    DEVELOPER = "developer"
    MANAGER = "manager"
    ADMIN = "admin"


class IssueStatus(str, Enum):
    """Issue status enumeration with state machine transitions."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

    @classmethod
    def get_valid_transitions(cls) -> dict["IssueStatus", list["IssueStatus"]]:
        """Get valid state transitions.

        State machine:
            open -> in_progress -> resolved -> closed
                                           -> reopened (from resolved or closed)
            reopened -> in_progress
        """
        return {
            cls.OPEN: [cls.IN_PROGRESS],
            cls.IN_PROGRESS: [cls.RESOLVED],
            cls.RESOLVED: [cls.CLOSED, cls.REOPENED],
            cls.CLOSED: [cls.REOPENED],
            cls.REOPENED: [cls.IN_PROGRESS],
        }

    def can_transition_to(self, target: "IssueStatus") -> bool:
        """Check if transition to target status is valid."""
        valid_targets = self.get_valid_transitions().get(self, [])
        return target in valid_targets


class IssuePriority(str, Enum):
    """Issue priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        """Get priority weight for sorting."""
        weights = {
            self.LOW: 1,
            self.MEDIUM: 2,
            self.HIGH: 3,
            self.CRITICAL: 4,
        }
        return weights[self]
