# -*- coding: utf-8 -*-
import enum
from typing import Any

from pydantic import BaseModel


class RangeGroupOperator(enum.Enum):
    GT = "greater than"
    GTE = "greater than or equal"
    LT = "less than"
    LTE = "less than or equal"


class RangeGroupData(BaseModel):
    left_val: Any
    right_val: Any
    left_operator: RangeGroupOperator
    right_operator: RangeGroupOperator
