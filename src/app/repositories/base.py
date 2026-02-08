"""Base repository with generic CRUD operations."""

from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# Type variable for model
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository implementing generic CRUD operations.

    Uses Repository pattern to abstract data access layer.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field: str,
        value: Any,
    ) -> Optional[ModelType]:
        """Get a single record by field value.

        Args:
            field: Field name
            value: Field value to match

        Returns:
            Model instance or None if not found
        """
        column = getattr(self.model, field)
        result = await self.session.execute(
            select(self.model).where(column == value)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_many(
        self,
        ids: List[UUID],
    ) -> List[ModelType]:
        """Get multiple records by IDs.

        Args:
            ids: List of UUIDs

        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        return list(result.scalars().all())

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record.

        Args:
            obj_in: Dictionary with model data

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        """Update an existing record.

        Args:
            db_obj: Existing model instance
            obj_in: Dictionary with updated data

        Returns:
            Updated model instance
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Delete a record.

        Args:
            db_obj: Model instance to delete
        """
        await self.session.delete(db_obj)
        await self.session.flush()

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Count records with optional filters.

        Args:
            filters: Optional dictionary of field-value pairs

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if value is not None:
                    column = getattr(self.model, field)
                    query = query.where(column == value)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists.

        Args:
            id: Record UUID

        Returns:
            True if record exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0

    def _apply_sorting(
        self,
        query: Select,
        sort_field: str,
        sort_desc: bool = False,
    ) -> Select:
        """Apply sorting to query.

        Args:
            query: SQLAlchemy select query
            sort_field: Field name to sort by
            sort_desc: Sort descending if True

        Returns:
            Query with sorting applied
        """
        column = getattr(self.model, sort_field, None)
        if column is not None:
            order_func = desc if sort_desc else asc
            query = query.order_by(order_func(column))
        return query

    def _apply_pagination(
        self,
        query: Select,
        page: int,
        page_size: int,
    ) -> Select:
        """Apply pagination to query.

        Args:
            query: SQLAlchemy select query
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Query with pagination applied
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
