"""Unit tests for issue service."""

import pytest

from app.models.enums import IssueStatus, IssuePriority


class TestIssueStatusTransitions:
    """Test issue status state machine transitions."""

    def test_open_can_transition_to_in_progress(self):
        """Test open -> in_progress is valid."""
        assert IssueStatus.OPEN.can_transition_to(IssueStatus.IN_PROGRESS)

    def test_open_cannot_transition_to_resolved(self):
        """Test open -> resolved is invalid."""
        assert not IssueStatus.OPEN.can_transition_to(IssueStatus.RESOLVED)

    def test_open_cannot_transition_to_closed(self):
        """Test open -> closed is invalid."""
        assert not IssueStatus.OPEN.can_transition_to(IssueStatus.CLOSED)

    def test_in_progress_can_transition_to_resolved(self):
        """Test in_progress -> resolved is valid."""
        assert IssueStatus.IN_PROGRESS.can_transition_to(IssueStatus.RESOLVED)

    def test_resolved_can_transition_to_closed(self):
        """Test resolved -> closed is valid."""
        assert IssueStatus.RESOLVED.can_transition_to(IssueStatus.CLOSED)

    def test_resolved_can_transition_to_reopened(self):
        """Test resolved -> reopened is valid."""
        assert IssueStatus.RESOLVED.can_transition_to(IssueStatus.REOPENED)

    def test_closed_can_transition_to_reopened(self):
        """Test closed -> reopened is valid."""
        assert IssueStatus.CLOSED.can_transition_to(IssueStatus.REOPENED)

    def test_reopened_can_transition_to_in_progress(self):
        """Test reopened -> in_progress is valid."""
        assert IssueStatus.REOPENED.can_transition_to(IssueStatus.IN_PROGRESS)

    def test_closed_cannot_transition_to_open(self):
        """Test closed -> open is invalid."""
        assert not IssueStatus.CLOSED.can_transition_to(IssueStatus.OPEN)


class TestIssuePriority:
    """Test issue priority."""

    def test_priority_weights(self):
        """Test priority weights for sorting."""
        assert IssuePriority.LOW.weight < IssuePriority.MEDIUM.weight
        assert IssuePriority.MEDIUM.weight < IssuePriority.HIGH.weight
        assert IssuePriority.HIGH.weight < IssuePriority.CRITICAL.weight

    def test_critical_is_highest_priority(self):
        """Test critical has highest weight."""
        assert IssuePriority.CRITICAL.weight == 4
