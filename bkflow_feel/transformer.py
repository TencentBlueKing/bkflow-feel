# -*- coding: utf-8 -*-
from lark import Token, Transformer, v_args

from .data_models import RangeGroupOperator
from .parsers import (
    AfterFunc,
    And,
    BeforeFunc,
    Between,
    Boolean,
    Context,
    ContextItem,
    Date,
    DateAndTime,
    DayOfWeekFunc,
    Expr,
    FuncInvocation,
    FunctionCall,
    In,
    IncludesFunc,
    List,
    ListEvery,
    ListFilter,
    ListItem,
    ListOperator,
    ListSome,
    MonthOfYearFunc,
    Not,
    NotEqual,
    NowFunc,
    Null,
    Number,
    Or,
    Pair,
    RangeGroup,
    SameTypeBinaryOperator,
    String,
    StringOperator,
    Time,
    TodayFunc,
    ToString,
    TZInfo,
    Variable, IsDefinedFunc, GetOrElseFunc,
)


@v_args(inline=True)
class FEELTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def number(self, token):
        try:
            value = int(token.value)
        except ValueError:
            value = float(token.value)
        return Number(value)

    def string(self, value):
        return String(value[1:-1])

    def true(self):
        return Boolean(True)

    def false(self):
        return Boolean(False)

    def null(self):
        return Null()

    def expr(self, item):
        return Expr(item)

    def list_(self, *items):
        return List(*items)

    def list_filter(self, list_expr, filter_expr):
        return ListFilter(list_expr, filter_expr)

    def list_item(self, list_expr, index):
        return ListItem(list_expr=list_expr, index=int(index.value))

    def list_some(self, *items):
        expr = items[-1]
        iter_pairs = [(items[i], items[i + 1]) for i in range(0, len(items) - 1, 2)]
        return ListSome(iter_pairs, expr)

    def list_every(self, *items):
        expr = items[-1]
        iter_pairs = [(items[i], items[i + 1]) for i in range(0, len(items) - 1, 2)]
        return ListEvery(iter_pairs, expr)

    def range_atom(self, value):
        if isinstance(value, Token):
            if value.type == "SIGNED_INT":
                return Number(int(value.value))
            elif value.type == "NAME":
                return Variable(value.value)
        return value

    def close_range_group(self, start, end):
        return RangeGroup(start, end, RangeGroupOperator.GTE, RangeGroupOperator.LTE)

    def open_range_group(self, start, end):
        return RangeGroup(start, end, RangeGroupOperator.GT, RangeGroupOperator.LT)

    def left_open_range_group(self, start, end):
        return RangeGroup(start, end, RangeGroupOperator.GT, RangeGroupOperator.LTE)

    def right_open_range_group(self, start, end):
        return RangeGroup(start, end, RangeGroupOperator.GTE, RangeGroupOperator.LT)

    def variable(self, name_token):
        return Variable(name_token.value)

    def function_call(self, name, *args):
        return FunctionCall(name, args)

    def add(self, left, right):
        return SameTypeBinaryOperator("add", left, right)

    def sub(self, left, right):
        return SameTypeBinaryOperator("subtract", left, right)

    def mul(self, left, right):
        return SameTypeBinaryOperator("multiply", left, right)

    def div(self, left, right):
        return SameTypeBinaryOperator("divide", left, right)

    def pow(self, left, right):
        return SameTypeBinaryOperator("power", left, right)

    def eq(self, left, right):
        return SameTypeBinaryOperator("equal", left, right)

    def ne(self, left, right):
        return NotEqual(left, right)

    def lt(self, left, right):
        return SameTypeBinaryOperator("less_than", left, right)

    def gt(self, left, right):
        return SameTypeBinaryOperator("greater_than", left, right)

    def lte(self, left, right):
        return SameTypeBinaryOperator("less_than_or_equal", left, right)

    def gte(self, left, right):
        return SameTypeBinaryOperator("greater_than_or_equal", left, right)

    def and_(self, left, right):
        return And(left, right)

    def or_(self, left, right):
        return Or(left, right)

    def between(self, target, left, right):
        return Between(target, left, right)

    def in_(self, left, right):
        return In(left, right)

    def not_func(self, value):
        return Not(value)

    def date(self, value):
        return Date(value)

    def date_func(self, value):
        return Expr(value)

    def timezone(self, value):
        return Expr(value)

    def tz_offset(self, token):
        return TZInfo("offset", token.value)

    def tz_name(self, *tokens):
        if len(tokens) == 2:
            name = f"{tokens[0].value}/{tokens[1].value}"
        else:
            name = "UTC"
        return TZInfo("name", name)

    def time(self, value, timezone=None):
        return Time(value, timezone)

    def date_and_time(self, date, time):
        return DateAndTime(date, time)

    def time_func(self, value):
        return Expr(value)

    def date_and_time_func(self, value):
        return Expr(value)

    def now_func(self):
        return NowFunc()

    def today_func(self):
        return TodayFunc()

    def day_of_week_func(self, value):
        return DayOfWeekFunc(value)

    def month_of_year_func(self, value):
        return MonthOfYearFunc(value)

    def before_func(self, left, right):
        return BeforeFunc(left, right)

    def after_func(self, left, right):
        return AfterFunc(left, right)

    def includes_func(self, left, right):
        return IncludesFunc(left, right)

    def get_or_else_func(self, value, default):
        return GetOrElseFunc(value, default)

    def is_defined_func(self, value):
        return IsDefinedFunc(value)

    def context(self, *args):
        return Context(args)

    def context_item(self, expr, *keys):
        return ContextItem(expr, keys)

    def pair(self, key_token, value):
        return Pair(key=String(key_token.value.strip('"')), value=value)

    def bracket(self, value):
        return Expr(value)

    def to_string(self, value):
        return ToString(value)

    def contains(self, left, right):
        return StringOperator("contains", left, right)

    def starts_with(self, left, right):
        return StringOperator("starts_with", left, right)

    def ends_with(self, left, right):
        return StringOperator("ends_with", left, right)

    def matches(self, left, right):
        return StringOperator("matches", left, right)

    def list_contains(self, *expr):
        return ListOperator("list_contains", *expr)

    def list_count(self, *expr):
        return ListOperator("list_count", *expr)

    def list_all(self, *expr):
        return ListOperator("list_all", *expr)

    def list_any(self, *expr):
        return ListOperator("list_any", *expr)

    def func_invocation(self, func_name, *args):
        func_name = " ".join([token.value for token in func_name.children])
        if len(args) == 1 and getattr(args[0], "data", None) and args[0].data.value == "named_args":
            args_pairs = args[0].children
            named_args = {args_pairs[i].value: args_pairs[i + 1] for i in range(0, len(args_pairs), 2)}
            return FuncInvocation(func_name, named_args=named_args)
        return FuncInvocation(func_name, args=args)
