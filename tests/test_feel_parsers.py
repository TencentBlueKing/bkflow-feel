# -*- coding: utf-8 -*-
import datetime

import pytest
import pytz

from bkflow_feel.api import parse_expression
from bkflow_feel.utils import FEELFunctionsManager

NULL_DATA = [("null", {}, None)]
NUMBER_DATA = [
    ("3", {}, 3),
    ("-4", {}, -4),
    ("3.14", {}, 3.14),
    ("1+2", {}, 3),
    ("1+2*3", {}, 7),
    ("2*3+1", {}, 7),
    ("a+b", {"a": 1, "b": 2}, 3),
]
STRING_DATA = [
    ('""', {}, ""),
    ('"hello"', {}, "hello"),
    ('"order-" + string(123)', {}, "order-123"),
    ('"order-" + string(123.1)', {}, "order-123.1"),
    ('starts with("abc", "a")', {}, True),
    ('starts with("abc", "b")', {}, False),
    ('ends with("cba", "a")', {}, True),
    ('ends with("cba", "b")', {}, False),
    ('matches("foobar", "^fo*bar")', {}, True),
    ('contains("abc", "b")', {}, True),
    ('contains("abc", "d")', {}, False),
]
BOOLEAN_DATA = [
    ("true", {}, True),
    ("false", {}, False),
    ("1 = 1", {}, True),
    ("1 != 1", {}, False),
    ("2 > 1", {}, True),
    ("2 < 1", {}, False),
    ("1 >= 1", {}, True),
    ("1 <= 1", {}, True),
    ("5 between 3 and 7", {}, True),
    ("5 between 3 and 7 and true", {}, True),
    ("true and false", {}, False),
    ("false or false", {}, False),
]
LIST_DATA = [
    ("[]", {}, []),
    ("[1, 2, 3]", {}, [1, 2, 3]),
    ('["a", "b"]', {}, ["a", "b"]),
    ('[["list"], "of", [["list"]]]', {}, [["list"], "of", [["list"]]]),
    ("[1,2,3,4][-1]", {}, 4),
    ("[1,2,3,4][-5]", {}, None),
    ("[1,2,3,4][1]", {}, 1),
    ("[1,2,3,4][5]", {}, None),
    ("[1,2,3,4][item > 2]", {}, [3, 4]),
    ("[1,2,3,4][item > 10]", {}, []),
    ("[{x:1, y:2}, {x:2, y:3}][x=1]", {}, [{"x": 1, "y": 2}]),
    ("[{x:1, y:2}, {x:2, y:3}, {y:3}][x>1]", {}, [{"x": 2, "y": 3}]),
    ("[{x:1, y:2}, {x:2, y:3}, {y:3}][x>1]", {"x": 50}, [{"x": 2, "y": 3}]),
    ("all([true, false])", {}, False),
    ("all([false, false])", {}, False),
    ("all([true, true])", {}, True),
    ("any([true, false])", {}, True),
    ("any([false, false])", {}, False),
    ("any([true, true])", {}, True),
    ("count([])", {}, 0),
    ("count([1,2,3,4])", {}, 4),
    ("list contains([1, 2, 3], 2)", {}, True),
    ("list contains([1, 2, 3], 5)", {}, False),
    ("some x in [1,2,3] satisfies x > 2", {}, True),
    ("some x in [4,4,3], y in [2,3,4] satisfies x < y", {}, True),
    ("some x in [1,2,3], y in [2,3,4], z in [0,0,0] satisfies x > (y+z)", {}, False),
    ("every x in [1,2,3] satisfies x > 2", {}, False),
    ("every x in [4,4,3], y in [2,3,4] satisfies x < y", {}, False),
    ("every x in [4,4,5], y in [2,3,4] satisfies x > y", {}, True),
    ("every x in [1,2,3], y in [2,3,4], z in [0,0,0] satisfies x > (y+z)", {}, False),
    ("every x in [1,2,3], y in [2,3,4], z in [0,0,0] satisfies y > (x+z)", {}, True),
    ("every x in [1,2,3], y in [2,3,4,5], z in [0,0,0] satisfies y > (x+z)", {}, None),
]
CONTEXT_DATA = [
    ("{}", {}, {}),
    ('{"a": 1, "b": 2}', {}, {"a": 1, "b": 2}),
    ('{"a": 1, "b": 2}.a', {}, 1),
    ('{"a": 1, "b": 2}.a', {"a": 4}, 1),
    ('{"a": {"c": 3}, "b": 2}.a.c', {}, 3),
    ("{a: 1, b: 2}", {}, {"a": 1, "b": 2}),
    ("{a: 1, b: 2}.a", {}, 1),
    ("{a: 1, b: 2}.a", {"a": 2}, 1),
    ("{a: a, b: 2}.a", {"a": 2}, 2),
    ('{a: {"c": 3}, b: 2}.a.c', {}, 3),
    ("{a: {c: 3}, b: 2}.a.c", {}, 3),
    ("{a: {c: 3}, b: 2}.c", {}, None),
    ("{a: {c: 3}, b: 2}.a.d", {}, None),
    ("[{a: 1, b: 2},{a: 2,b: 10}][b<7]", {}, [{"a": 1, "b": 2}]),
]
RANGE_DATA = [
    ("5 in [1,3,5,7]", {}, True),
    ("5 in [1..10]", {}, True),
    ("3 in [1..3]", {}, True),
    ("5 in [1..3]", {}, False),
    ("1 in (1..3]", {}, False),
    ("3 in [1..3)", {}, False),
    ("2 in (1..3)", {}, True),
    ("5 in (1..3]", {}, False),
    ("1.2 in (-1.1..3.2)", {}, True),
    ("1.2 in (-1.2..1.2)", {}, False),
    ("-1.3 in (-1.2..1.2)", {}, False),
    ("1.2 in (-1.1..1.2]", {}, True),
    ("0 in [-1.1..100)", {}, True),
    (
        'date and time("2023-02-01T00:00:00") in '
        '[date and time("2023-01-01T00:00:00")..date and time("2023-03-01T00:00:00")]',
        {},
        True,
    ),
    (
        'date and time("2023-03-01T00:00:00") in '
        '[date and time("2023-01-01T00:00:00")..date and time("2023-03-01T00:00:00")]',
        {},
        True,
    ),
]
BUILD_IN_FUNCS = [
    ('date("2017-03-10")', {}, datetime.date(year=2017, month=3, day=10)),
    ('time("00:00:00")', {}, datetime.time(hour=0, minute=0, second=0)),
    (
        'time("00:00:00Z")',
        {},
        datetime.time(hour=0, minute=0, second=0, tzinfo=pytz.UTC),
    ),
    (
        'time("00:00:00@America/Los_Angeles")',
        {},
        datetime.time(hour=0, minute=0, second=0, tzinfo=pytz.timezone("America/Los_Angeles")),
    ),
    (
        'time("00:00:00+08:00")',
        {},
        datetime.time(hour=0, minute=0, second=0, tzinfo=pytz.FixedOffset(480)),
    ),
    (
        'time("00:00:00-08:10")',
        {},
        datetime.time(hour=0, minute=0, second=0, tzinfo=pytz.FixedOffset(-490)),
    ),
    (
        'date and time("2017-03-10T00:00:00")',
        {},
        datetime.datetime(year=2017, month=3, day=10, hour=0, minute=0, second=0),
    ),
    (
        'date and time("2017-03-10T00:00:00 +08:00")',
        {},
        datetime.datetime(
            year=2017,
            month=3,
            day=10,
            hour=0,
            minute=0,
            second=0,
            tzinfo=pytz.FixedOffset(480),
        ),
    ),
    (
        'date and time("2021-01-01T00:00:00@America/Los_Angeles")',
        {},
        datetime.datetime(
            year=2021,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            tzinfo=pytz.timezone("America/Los_Angeles"),
        ),
    ),
    (
        'date and time("2022-01-01T00:00:00+08:00") < date and time("2022-01-01T00:00:00Z")',
        {},
        True,
    ),
    ("today()", {}, datetime.date.today()),
    ('day of week(date("2023-08-21"))', {}, "Monday"),
    ('day of week(date and time("2023-08-21T00:00:00"))', {}, "Monday"),
    ('month of year(date("2019-09-17"))', {}, "September"),
    ("before(1,10)", {}, True),
    ("before(10,1)", {}, False),
    ("before([1..5],10)", {}, True),
    ("before(1,[2..5])", {}, True),
    ("before((1..5),5)", {}, True),
    ("before(2,(2..5])", {}, True),
    ("before(2,[2..5])", {}, False),
    ("before([1..5], [6..10])", {}, True),
    ("before([1..5], [3..10])", {}, False),
    ("after(12, [2..5])", {}, True),
    ("after([2..5], 12)", {}, False),
    ("after([6..10], [1..5])", {}, True),
    ("after([5..10], [1..5])", {}, False),
    ("after((5..10], [1..5])", {}, True),
    ("includes([5..10], 6)", {}, True),
    ("includes([5..10], 6)", {}, True),
    ("includes([3..4], 5)", {}, False),
    ("includes([1..10], [4..6])", {}, True),
    ("includes([5..8], [1..5])", {}, False),
    ("includes([1..10], (1..10))", {}, True),
    ("includes([1..5), [1..5])", {}, False),
    ("is defined(1)", {}, True),
    ("is defined(null)", {}, False),
    ("is defined(x)", {}, False),
    ("is defined(x)", {"x": 1}, True),
    ("is defined(x.y)", {"x": 1}, False),
    ('get or else(null, "abc")', {}, "abc"),
    ("get or else(0, 1)", {}, 0),
    ("get or else(null, null)", {}, None),
    ("not(true)", {}, False),
    ("not(false)", {}, True),
    ("not(null)", {}, True),
]

DEFINED_FUNCS = [
    ("func not exist()", {}, None),
    ("func without params()", {}, "Without params"),
    ("func with params(1,2,3)", {}, "With params: 1, 2, 3"),
    ("func with named params(a:1,b:2,c:3)", {}, "With named params: 1, 2, 3"),
    ("hello world()", {}, "Hello world"),
    (
        "hello world with params(1, 2)",
        {},
        {"a": 1, "b": 2, "c": 2, "args": (), "kwargs": {}},
    ),
    (
        "hello world with params(a:1, b:2)",
        {},
        {"a": 1, "b": 2, "c": 2, "args": (), "kwargs": {}},
    ),
    (
        "hello world with params(1, 2, 3, 4)",
        {},
        {"a": 1, "b": 2, "c": 3, "args": (4,), "kwargs": {}},
    ),
    (
        "hello world with params(a:1, b:2, c:3, d:4)",
        {},
        {"a": 1, "b": 2, "c": 3, "args": (), "kwargs": {"d": 4}},
    ),
    ("func with inputs validation(1,2,3,4)", {}, {"a": 1, "b": 2, "args": (3, 4), "kwargs": {}}),
    ("func with inputs validation(1,2,3,4,5)", {}, None),
    ("func with inputs validation(a:1, b:2, c:3)", {}, {"a": 1, "b": 2, "args": (), "kwargs": {"c": 3}}),
    ("func with inputs validation(1,2)", {}, None),
    ("func with single param(1)", {}, 1),
    ("func with single param(b:1)", {}, 1),
]


test_data = [
    *NULL_DATA,
    *NUMBER_DATA,
    *STRING_DATA,
    *BOOLEAN_DATA,
    *LIST_DATA,
    *CONTEXT_DATA,
    *RANGE_DATA,
    *BUILD_IN_FUNCS,
    *DEFINED_FUNCS,
]

REGISTER_FUNCS = {
    "func without params": "tests.functions.func_without_params",
    "func with params": "tests.functions.func_with_params",
    "func with named params": "tests.functions.func_with_named_params",
}
FEELFunctionsManager.register_funcs(REGISTER_FUNCS)


@pytest.mark.parametrize(
    "expression, context, expected",
    test_data,
)
def test_feel_parsers(expression, context, expected):
    result = parse_expression(expression, context=context, raise_exception=False)
    assert result == expected


@pytest.mark.parametrize(
    "expression, context, expected",
    test_data,
)
def test_feel_parsers_benchmark(benchmark, expression, context, expected):
    result = benchmark(parse_expression, expression, context=context, raise_exception=False)
    assert result == expected
