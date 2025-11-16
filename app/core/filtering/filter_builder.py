from datetime import datetime
from typing import Generic, Optional, TypeVar

from fastapi import Query as FastAPIQuery
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import Query

from app.core.filtering.filters import Order

T = TypeVar("T")


class FilterBuilder(Generic[T]):
    """
    Factory class to build SQLAlchemy queries with various filters
    and sorting options. It allows for dynamic query construction based on
    the provided model and filter criteria.

    Can use:
    - text filters for string fields
    - boolean filters for boolean fields
    - date range filters for datetime fields
    - range filters for numeric fields
    - ordering by specified fields
    - equality checks for specific fields
    """

    def __init__(self, model: type[T]):
        self.model = model
        self.filters = []
        self.sort_column = None
        self.sort_direction = Order.none

    def text(self, field_name: str, value: Optional[str]) -> None:
        if value:
            self.filters.append(getattr(self.model, field_name).ilike(f"%{value}%"))

    def boolean(self, field_name: str, value: Optional[bool]) -> None:
        if value is not None:
            self.filters.append(getattr(self.model, field_name) == value)

    def equal_to(self, field_name: str, value: Optional[str]) -> None:
        if value is not None:
            self.filters.append(getattr(self.model, field_name) == value)

    def daterange(
        self, field_name: str, start_date: datetime, end_date: datetime
    ) -> None:
        if start_date or end_date:
            date_filter = []
            if start_date:
                date_filter.append(getattr(self.model, field_name) >= start_date)
            if end_date:
                date_filter.append(getattr(self.model, field_name) <= end_date)
            self.filters.append(and_(*date_filter))

    def range(
        self,
        field_name: str,
        min_value: Optional[float],
        max_value: Optional[float],
    ) -> None:
        if min_value is not None or max_value is not None:
            range_filter = []
            if min_value is not None:
                range_filter.append(getattr(self.model, field_name) >= min_value)
            if max_value is not None:
                range_filter.append(getattr(self.model, field_name) <= max_value)
            self.filters.append(and_(*range_filter))

    def order_by(
        self,
        order_by: Optional[str],
        direction: Optional[Order] = None,
    ) -> None:
        if direction is None:
            direction = FastAPIQuery(Order.none)
        if not order_by:
            return

        if not hasattr(self.model, order_by):
            raise ValueError(f"Invalid order_by field: {order_by}")

        self.sort_column = getattr(self.model, order_by)
        self.sort_direction = direction or Order.asc

    def build(self, query: Query) -> Query:
        if self.filters:
            query = query.filter(and_(*self.filters))

        if self.sort_column is not None:
            if self.sort_direction == Order.desc:
                query = query.order_by(desc(self.sort_column))
            else:
                query = query.order_by(asc(self.sort_column))

        return query
