from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Order(str, Enum):
    asc = "asc"
    desc = "desc"
    none = "none"


class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
