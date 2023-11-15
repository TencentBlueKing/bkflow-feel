# -*- coding: utf-8 -*-
import abc
import datetime
import logging
import re

import pytz
from dateutil.parser import parse as date_parse

from .data_models import RangeGroupData, RangeGroupOperator
from .utils import FEELFunctionsManager
from .validators import BinaryOperationValidator, DummyValidator, ListsLengthValidator

logger = logging.getLogger(__name__)


class Expression(metaclass=abc.ABCMeta):
    validator_cls = DummyValidator

    @abc.abstractmethod
    def evaluate(self, context):
        pass


class CommonExpression(Expression):
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return self.value


class Expr(CommonExpression):
    def evaluate(self, context):
        return self.value.evaluate(context)


class Number(CommonExpression):
    pass


class String(CommonExpression):
    pass


class Boolean(CommonExpression):
    pass


class Null(Expression):
    def evaluate(self, context):
        return None


class List(Expression):
    def __init__(self, *items):
        self.items = items

    def evaluate(self, context):
        return [item.evaluate(context) for item in self.items]


class ListItem(Expression):
    def __init__(self, list_expr, index):
        self.list_expr = list_expr
        self.index = index

    def evaluate(self, context):
        items = self.list_expr.evaluate(context)
        if not isinstance(items, list) or self.index == 0 or len(items) < abs(self.index):
            return None
        items = items[self.index - 1] if self.index > 0 else items[self.index]
        return items


class ListMatch(Expression):
    validator_cls = ListsLengthValidator

    def __init__(self, iter_pairs, expr):
        self.iter_pairs = iter_pairs
        self.expr = expr

    def evaluate_and_validate_iter_pairs(self, context):
        iter_pairs = [(pair[0].value, pair[1].evaluate(context)) for pair in self.iter_pairs]
        self.validator_cls()(lists=[pair[1] for pair in iter_pairs])
        return iter_pairs


class ListEvery(ListMatch):
    def evaluate(self, context):
        iter_pairs = self.evaluate_and_validate_iter_pairs(context)
        for i in range(0, len(iter_pairs[0][1])):
            tmp_context = {**context, **{pair[0]: pair[1][i] for pair in iter_pairs}}
            if self.expr.evaluate(tmp_context) is False:
                return False
        return True


class ListSome(ListMatch):
    def evaluate(self, context):
        iter_pairs = self.evaluate_and_validate_iter_pairs(context)
        for i in range(0, len(iter_pairs[0][1])):
            tmp_context = {**context, **{pair[0]: pair[1][i] for pair in iter_pairs}}
            if self.expr.evaluate(tmp_context) is True:
                return True
        return False


class ListFilter(Expression):
    def __init__(self, list_expr, filter_expr):
        self.list_expr = list_expr
        self.filter_expr = filter_expr

    def evaluate(self, context):
        items = self.list_expr.evaluate(context)
        if not isinstance(items, list):
            return None
        result = []
        for item in items:
            try:
                # 当 item 为 dict 且 filter 中对比的 key 缺失时，可能报错
                if self.filter_expr.evaluate(item if isinstance(item, dict) else {"item": item}):
                    result.append(item)
            except Exception as e:
                logger.exception(e)
                pass
        return result


class Pair(Expression):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def evaluate(self, context):
        return self.key.evaluate(context), self.value.evaluate(context)


class Context(Expression):
    def __init__(self, pairs):
        self.pairs = pairs

    def evaluate(self, context):
        return dict(pair.evaluate(context) for pair in self.pairs)


class ContextItem(Expression):
    def __init__(self, expr, keys):
        self.expr = expr
        self.keys = keys

    def evaluate(self, context):
        result = self.expr.evaluate(context)
        for key in self.keys:
            if not isinstance(result, dict):
                return None
            result = result.get(key)
        return result


class Variable(Expression):
    def __init__(self, name):
        self.name = name

    def evaluate(self, context):
        return context.get(self.name)


class FunctionCall(Expression):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def evaluate(self, context):
        function = context.get(self.name)
        if function is None:
            raise ValueError(f"Unknown function: {self.name}")
        return function(*[arg.evaluate(context) for arg in self.args])


class BinaryOperator(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class SameTypeBinaryOperator(BinaryOperator):
    validator_cls = BinaryOperationValidator

    def __init__(self, operation, left, right):
        super().__init__(left, right)
        self.operation = operation

    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        self.validator_cls()(left_val, right_val)
        return getattr(self, self.operation)(left_val, right_val)

    def add(self, left_val, right_val):
        return left_val + right_val

    def subtract(self, left_val, right_val):
        return left_val - right_val

    def multiply(self, left_val, right_val):
        return left_val * right_val

    def divide(self, left_val, right_val):
        return left_val / right_val

    def power(self, left_val, right_val):
        return left_val**right_val

    def equal(self, left_val, right_val):
        return left_val == right_val

    def less_than(self, left_val, right_val):
        return left_val < right_val

    def greater_than(self, left_val, right_val):
        return left_val > right_val

    def less_than_or_equal(self, left_val, right_val):
        return left_val <= right_val

    def greater_than_or_equal(self, left_val, right_val):
        return left_val >= right_val


class NotEqual(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) != self.right.evaluate(context)


class And(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)


class Or(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)


class In(BinaryOperator):
    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        if isinstance(self.right, RangeGroup):
            left_operation = (
                left_val > right_val.left_val
                if right_val.left_operator == RangeGroupOperator.GT
                else left_val >= right_val.left_val
            )
            right_operation = (
                left_val < right_val.right_val
                if right_val.right_operator == RangeGroupOperator.LT
                else left_val <= right_val.right_val
            )
            return left_operation and right_operation
        return left_val in right_val


class Between(Expression):
    def __init__(self, value, left, right):
        self.value = value
        self.min = left
        self.max = right

    def evaluate(self, context):
        value = self.value.evaluate(context)
        return self.min.evaluate(context) <= value <= self.max.evaluate(context)


class RangeGroup(BinaryOperator):
    def __init__(self, left, right, left_operator, right_operator):
        self.left = left
        self.right = right
        self.left_operator = left_operator
        self.right_operator = right_operator

    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        data = {
            "left_val": left_val,
            "right_val": right_val,
            "left_operator": self.left_operator,
            "right_operator": self.right_operator,
        }
        return RangeGroupData(**data)


class BeforeFunc(BinaryOperator):
    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        operator = None
        if isinstance(self.left, RangeGroup):
            if left_val.right_operator == RangeGroupOperator.LT:
                operator = RangeGroupOperator.GTE
            left_val = left_val.right_val
        if isinstance(self.right, RangeGroup):
            if right_val.left_operator == RangeGroupOperator.GT:
                operator = RangeGroupOperator.GTE
            right_val = right_val.left_val

        if operator == RangeGroupOperator.GTE:
            return left_val <= right_val

        return left_val < right_val


class AfterFunc(BinaryOperator):
    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        operator = None
        if isinstance(self.left, RangeGroup):
            if left_val.left_operator == RangeGroupOperator.GT:
                operator = RangeGroupOperator.GTE
            left_val = left_val.left_val
        if isinstance(self.right, RangeGroup):
            if right_val.right_operator == RangeGroupOperator.LT:
                operator = RangeGroupOperator.GTE
            right_val = right_val.right_val
        if operator == RangeGroupOperator.GTE:
            return left_val >= right_val
        return left_val > right_val


class IncludesFunc(BinaryOperator):
    def evaluate(self, context):
        left_val: RangeGroupData = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        if isinstance(self.right, RangeGroup):
            left_operation = left_val.left_val <= right_val.left_val
            if left_val.left_operator == RangeGroupOperator.GT and right_val.left_operator == RangeGroupOperator.GTE:
                left_operation = left_val.left_val < right_val.left_val
            right_operation = left_val.right_val >= right_val.right_val
            if left_val.right_operator == RangeGroupOperator.LT and right_val.right_operator == RangeGroupOperator.LTE:
                right_operation = left_val.right_val > right_val.right_val
        else:
            left_operation = left_val.left_val <= right_val
            if left_val.left_operator == RangeGroupOperator.GT:
                left_operation = left_val.left_val < right_val
            right_operation = left_val.right_val >= right_val
            if left_val.right_operator == RangeGroupOperator.LT:
                right_operation = left_val.right_val > right_val
        return left_operation and right_operation


class GetOrElseFunc(BinaryOperator):
    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        return left_val if left_val is not None else right_val


class IsDefinedFunc(CommonExpression):
    def evaluate(self, context):
        return self.value.evaluate(context) is not None


class Not(Expression):
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return not self.value.evaluate(context)


class Date(CommonExpression):
    def evaluate(self, context):
        year, month, day = self.value.split("-")
        return datetime.date(int(year), int(month), int(day))


class TZInfo(Expression):
    def __init__(self, method, value):
        self.method = method
        self.value = value

    def evaluate(self, context):
        if self.method == "name":
            return pytz.timezone(self.value)
        elif self.method == "offset":
            hours, minutes = map(int, self.value.split(":"))
            sign = -1 if hours < 0 else 1
            hours = abs(hours)
            offset = hours * 60 + minutes
            return pytz.FixedOffset(sign * offset)


class Time(Expression):
    def __init__(self, value, timezone: TZInfo = None):
        self.value = value
        self.timezone = timezone

    def evaluate(self, context):
        parsed_dt = date_parse(self.value)
        timezone = self.timezone.evaluate(context) if self.timezone is not None else None
        return datetime.time(parsed_dt.hour, parsed_dt.minute, parsed_dt.second, tzinfo=timezone)


class DateAndTime(Expression):
    def __init__(self, date: Date, time: Time):
        self.date = date
        self.time = time

    def evaluate(self, context):
        date = self.date.evaluate(context)
        time = self.time.evaluate(context)
        return datetime.datetime.combine(date, time, tzinfo=time.tzinfo)


class NowFunc(Expression):
    def evaluate(self, context):
        # TODO：带时区需要配置
        return datetime.datetime.now()


class TodayFunc(Expression):
    def evaluate(self, context):
        return datetime.date.today()


class DayOfWeekFunc(CommonExpression):
    WEEKDAYS = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    def evaluate(self, context):
        date_or_datetime = self.value.evaluate(context)
        return self.WEEKDAYS[date_or_datetime.weekday()]


class MonthOfYearFunc(CommonExpression):
    MONTH_MAPPING = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "Auguest",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    def evaluate(self, context):
        date_or_datetime = self.value.evaluate(context)
        return self.MONTH_MAPPING[date_or_datetime.month]


class ToString(CommonExpression):
    def evaluate(self, context):
        return str(self.value.evaluate(context))


class StringOperator(BinaryOperator):
    validator_cls = BinaryOperationValidator

    def __init__(self, operation, left, right):
        super().__init__(left, right)
        self.operation = operation

    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        self.validator_cls()(left_val, right_val, instance_type=str)
        return getattr(self, self.operation)(left_val, right_val)

    def contains(self, left_str, right_str):
        return right_str in left_str

    def starts_with(self, left_str, right_str):
        return left_str.startswith(right_str)

    def ends_with(self, left_str, right_str):
        return left_str.endswith(right_str)

    def matches(self, left_str, right_str):
        return re.match(right_str, left_str) is not None


class ListOperator(Expression):
    def __init__(self, operation, *expr):
        self.operation = operation
        self.expr = expr

    def evaluate(self, context):
        return getattr(self, self.operation)(context)

    def list_contains(self, context):
        list_ = self.expr[0].evaluate(context)
        item = self.expr[1].evaluate(context)
        return item in list_

    def list_count(self, context):
        list_ = self.expr[0].evaluate(context)
        return len(list_)

    def list_all(self, context):
        list_ = self.expr[0].evaluate(context)
        return all(list_)

    def list_any(self, context):
        list_ = self.expr[0].evaluate(context)
        return any(list_)


class FuncInvocation(Expression):
    def __init__(self, func_name, args=None, named_args=None):
        self.func_name = func_name
        self.args = args or []
        self.named_args = named_args or {}

    def evaluate(self, context):
        try:
            func = FEELFunctionsManager.get_func(self.func_name)
        except Exception as e:
            logger.exception(e)
            func = None
        if not func:
            return None

        if self.args:
            params = [arg.evaluate(context) for arg in self.args]
            return func(*params)
        elif self.named_args:
            params = {key: arg.evaluate(context) for key, arg in self.named_args.items()}
            return func(**params)

        return func()
