#!/usr/bin/env python3
"""Seed database with sample data for development/testing."""

import asyncio
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security.password import password_hasher
from app.models.user import User
from app.models.project import Project
from app.models.issue import Issue
from app.models.comment import Comment
from app.models.enums import UserRole, IssueStatus, IssuePriority


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """Create sample users."""
    users = {}

    user_data = [
        ("admin", "admin@tasktracker.com", UserRole.ADMIN),
        ("manager1", "manager1@tasktracker.com", UserRole.MANAGER),
        ("manager2", "manager2@tasktracker.com", UserRole.MANAGER),
        ("dev1", "dev1@tasktracker.com", UserRole.DEVELOPER),
        ("dev2", "dev2@tasktracker.com", UserRole.DEVELOPER),
        ("dev3", "dev3@tasktracker.com", UserRole.DEVELOPER),
    ]

    for username, email, role in user_data:
        user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hasher.hash("Password123!"),
            role=role,
            is_active=True,
        )
        session.add(user)
        users[username] = user

    await session.flush()
    print(f"Created {len(users)} users")
    return users


async def seed_projects(session: AsyncSession, users: dict[str, User]) -> list[Project]:
    """Create sample projects."""
    projects = []

    project_data = [
        ("Task Tracker API", "Internal bug tracking system API", "manager1"),
        ("Mobile App", "iOS and Android mobile application", "manager1"),
        ("Frontend Dashboard", "React-based admin dashboard", "manager2"),
        ("Infrastructure", "DevOps and cloud infrastructure", "manager2"),
        ("Documentation", "Technical documentation and guides", "manager1"),
    ]

    for name, description, creator in project_data:
        project = Project(
            id=uuid4(),
            name=name,
            description=description,
            created_by_id=users[creator].id,
            is_archived=False,
        )
        session.add(project)
        projects.append(project)

    await session.flush()
    print(f"Created {len(projects)} projects")
    return projects


async def seed_issues(
    session: AsyncSession,
    projects: list[Project],
    users: dict[str, User],
) -> list[Issue]:
    """Create sample issues."""
    issues = []

    issue_data = [
        # Task Tracker API issues
        (0, "Implement JWT authentication", IssueStatus.RESOLVED, IssuePriority.HIGH, "dev1", "dev1"),
        (0, "Add rate limiting middleware", IssueStatus.IN_PROGRESS, IssuePriority.MEDIUM, "dev1", "dev2"),
        (0, "Fix database connection pooling", IssueStatus.OPEN, IssuePriority.CRITICAL, "dev2", None),
        (0, "Add Swagger documentation", IssueStatus.CLOSED, IssuePriority.LOW, "dev3", "dev3"),
        # Mobile App issues
        (1, "Login screen not responsive", IssueStatus.OPEN, IssuePriority.HIGH, "dev2", "dev1"),
        (1, "Push notifications failing", IssueStatus.IN_PROGRESS, IssuePriority.CRITICAL, "dev1", "dev2"),
        (1, "Memory leak in image gallery", IssueStatus.REOPENED, IssuePriority.HIGH, "dev3", "dev3"),
        # Frontend Dashboard issues
        (2, "Add dark mode support", IssueStatus.OPEN, IssuePriority.LOW, "dev1", None),
        (2, "Charts not loading correctly", IssueStatus.RESOLVED, IssuePriority.MEDIUM, "dev2", "dev1"),
        (2, "Improve loading performance", IssueStatus.IN_PROGRESS, IssuePriority.MEDIUM, "dev3", "dev2"),
        # Infrastructure issues
        (3, "Set up Kubernetes cluster", IssueStatus.CLOSED, IssuePriority.HIGH, "dev1", "dev1"),
        (3, "Configure CI/CD pipeline", IssueStatus.RESOLVED, IssuePriority.HIGH, "dev2", "dev2"),
        (3, "Add monitoring and alerting", IssueStatus.OPEN, IssuePriority.MEDIUM, "dev3", None),
    ]

    for proj_idx, title, status, priority, reporter, assignee in issue_data:
        issue = Issue(
            id=uuid4(),
            title=title,
            description=f"Detailed description for: {title}",
            status=status,
            priority=priority,
            project_id=projects[proj_idx].id,
            reporter_id=users[reporter].id,
            assignee_id=users[assignee].id if assignee else None,
            due_date=date.today() + timedelta(days=14) if priority in [IssuePriority.HIGH, IssuePriority.CRITICAL] else None,
        )
        session.add(issue)
        issues.append(issue)

    await session.flush()
    print(f"Created {len(issues)} issues")
    return issues


async def seed_comments(
    session: AsyncSession,
    issues: list[Issue],
    users: dict[str, User],
) -> list[Comment]:
    """Create sample comments."""
    comments = []

    comment_data = [
        (0, "dev1", "Started working on this. Will update once done."),
        (0, "dev2", "Let me know if you need help with the testing."),
        (0, "manager1", "Great progress! Please add unit tests."),
        (1, "dev2", "Looking into this issue now."),
        (2, "dev1", "This is critical - needs immediate attention."),
        (2, "manager1", "Assigned to dev2. Please prioritize."),
        (5, "dev2", "Found the root cause. Working on a fix."),
        (5, "dev1", "Thanks for the quick response!"),
        (8, "dev1", "Fixed in commit abc123."),
        (8, "dev2", "Verified the fix. Looks good."),
    ]

    for issue_idx, author, content in comment_data:
        if issue_idx < len(issues):
            comment = Comment(
                id=uuid4(),
                content=content,
                issue_id=issues[issue_idx].id,
                author_id=users[author].id,
            )
            session.add(comment)
            comments.append(comment)

    await session.flush()
    print(f"Created {len(comments)} comments")
    return comments


async def seed_database():
    """Main function to seed the database."""
    print("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        try:
            # Create users
            users = await seed_users(session)

            # Create projects
            projects = await seed_projects(session, users)

            # Create issues
            issues = await seed_issues(session, projects, users)

            # Create comments
            await seed_comments(session, issues, users)

            # Commit all changes
            await session.commit()
            print("\nDatabase seeding completed successfully!")

            # Print login credentials
            print("\n" + "=" * 50)
            print("Sample Login Credentials:")
            print("=" * 50)
            print("Admin:    admin@tasktracker.com / Password123!")
            print("Manager:  manager1@tasktracker.com / Password123!")
            print("Developer: dev1@tasktracker.com / Password123!")
            print("=" * 50)

        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
