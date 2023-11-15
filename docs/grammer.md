# 支持 FEEL 语法

<!-- TOC -->

- [支持 FEEL 语法](#支持-feel-语法)
  - [基础类型](#基础类型)
    - [Null](#null)
    - [Boolean](#boolean)
    - [String](#string)
    - [Numeric](#numeric)
    - [List](#list)
    - [Context](#context)
    - [Date](#date)
    - [Time](#time)
    - [DateTime](#datetime)
  - [表达式](#表达式)
    - [布尔表达式](#布尔表达式)
    - [字符串表达式](#字符串表达式)
    - [数字表达式](#数字表达式)
    - [列表表达式](#列表表达式)
    - [上下文(Context) 表达式](#上下文context-表达式)
  - [函数](#函数)
    - [内置函数](#内置函数)
      - [not 函数](#not-函数)
      - [string 函数](#string-函数)
      - [contains 函数](#contains-函数)
      - [starts with 函数](#starts-with-函数)
      - [ends with 函数](#ends-with-函数)
      - [matches 函数](#matches-函数)
      - [list contains 函数](#list-contains-函数)
      - [count 函数](#count-函数)
      - [all 函数](#all-函数)
      - [any 函数](#any-函数)
      - [now 函数](#now-函数)
      - [today 函数](#today-函数)
      - [month of year 函数](#month-of-year-函数)
      - [day of week 函数](#day-of-week-函数)
      - [before 函数](#before-函数)
      - [after 函数](#after-函数)
      - [includes 函数](#includes-函数)
      - [get or else 函数](#get-or-else-函数)
      - [is defined 函数](#is-defined-函数)
    - [开发者自定义函数调用](#开发者自定义函数调用)

<!-- /TOC -->

## 基础类型

### Null

空值

Python 类型：None

```
null
```

### Boolean

布尔值

Python 类型：bool

```
true
false
```

### String

字符串

Python 类型：str

```
"hello"
```

### Numeric

数值

Python 类型：int/float

```
2
1.2
-2
```

### List

列表

Python 类型：list

```
[]
[1, 2, 3]
["abc", "efg"]
```

### Context

上下文，可以用于存储对象和属性

Python 类型：dict

```
{}

{a: 1, b: 2}

{"a": 1, "b": 2}
```

### Date

日期

格式：YYYY-MM-DD

Python 类型：datetime.date

```
date("2020-01-01")
```

### Time

时间

格式：HH:MM:SS

Python 类型：datetime.time

```
time("00:00:00")
```

### DateTime


日期时间

格式：YYYY-MM-DDTHH:MM:SS [ @timezone / timezone_offset ]

Python 类型: datetime.datetime

```
date and time("2017-03-10T00:00:00") // datetime.datetime(year=2017, month=3, day=10, hour=0, minute=0, second=0)

date and time("2017-03-10T00:00:00 +08:00") // datetime.datetime(year=2017, month=3, day=10, hour=0, minute=0, second=0, tzinfo=pytz.FixedOffset(480))

date and time("2021-01-01T00:00:00@America/Los_Angeles") // datetime.datetime(year=2021, month=1, day=1, hour=0, minute=0, second=0, tzinfo=pytz.timezone("America/Los_Angeles"))
```


## 表达式

### 布尔表达式

支持常见的比较运算

| 运算符 ｜ 说明 | 支持类型 | 
| --- ｜ --- | --- ｜ --- | 
| = ｜ 等于 | any | 
| != ｜ 不等于 | any | 
| > ｜ 大于 | number, date, time, date-time | 
| < ｜ 小于 | number, date, time, date-time | 
| >= ｜ 大于等于 | number, date, time, date-time | 
| <= ｜ 小于等于 | number, date, time, date-time |
| a between [b] and [c] | a介于b和c之间 | number, date, time, date-time |

```
1 = 1  // True

1 != 2 // True

1 > 2 // False

5 between 1 and 6 // True
```

支持 与/或 运算

```
true and true // True
true and false // False

true or true // True
true or false // True
```

### 字符串表达式

支持字符串拼接

```
"hello" + "world" // "helloworld"
```

支持 string() 转换

```
string(123) // "123"
```

### 数字表达式

支持 加减乘除 和 幂 运算

```
1 + 2 // 3
1 - 2 // -1
1 * 2 // 2
1 / 2 // 0.5
2 ** 3 // 8
```

### 列表表达式

下标取值

```
[1, 2, 3][1] // 1
[1, 2, 3][-1] // 3
```

元素过滤

```
[1, 2, 3][item < 3] // [1, 2]
```

Some 操作

```
some x in [1,2,3] satisfies x > 2 // True
```

Every 操作

```
every x in [1,2,3] satisfies x > 2 // False
```

### 上下文(Context) 表达式

```
{a: 1, b: 2} // {a:1, b:2}
{"a": 1, "b": 2} // {a:1, b:2}
```

取值

```
{a: 1, b: 2}.a // 1
```

元素过滤

```
[{a: 1, b: 2},{a: 2,b: 10}][b<7] // [{a:1,b:5}]
```

## 函数

### 内置函数

#### not 函数
对输入值取反，返回 bool

```
not(true) // False
not(false) // True
not(null) // True
``` 

#### string 函数
将输入值转换为字符串，返回 string

```
string(123) // "123"
string(true) // "True"
```

#### contains 函数
判断字符串中是否包含输入值，返回 bool

```
contains("abc", "b") // True
contains("abc", "d") // False
```

#### starts with 函数
判断字符串是否以输入值开头，返回 bool

```
starts with("abc", "a") // True
starts with("abc", "b") // False
```

#### ends with 函数
判断字符串是否以输入值结尾，返回 bool

```
ends with("abc", "c") // True
ends with("abc", "b") // False
```

#### matches 函数
判断字符串是否匹配输入正则表达式，返回 bool

```
matches("foobar", "^fo*bar") // True
```

#### list contains 函数
判断列表中是否包含输入值，返回 bool

```
list contains([1, 2, 3], 2) // True
```

#### count 函数
计算列表中元素个数

```
count([1, 2, 3]) // 3
```

#### all 函数
判断列表中所有元素是否都满足真值判断，返回 bool

```
all([true, true, true]) // True
all([true, true, true, false]) // False
```

#### any 函数
判断列表中是否有满足真值判断的元素，返回 bool

```
any([true, true, true]) // True
any([true, true, true, false]) // True
any([false, false, false]) // False
```

#### now 函数
获取当前时间，返回 datetime.datetime.now() 结果

```
now() // datetime.datetime.now()
```

#### today 函数
获取当前日期，返回 datetime.date.today() 结果

```
today() // datetime.date.today()
```

#### month of year 函数
根据输入的时间类型获取当前月份，返回 string

```
month of year(date("2023-09-01")) // "September"
month of year(date and time("2019-08-17T00:00:00")) // "August"
```

#### day of week 函数
根据输入的时间类型获取当前日期，返回 string

```
day of week(date("2023-09-01")) // "Friday"
day of week(date and time("2019-08-17T00:00:00")) // "Saturday"
```

#### before 函数
判断【参数1】是否在【参数2】之前，返回 bool

```
before(date and time("2023-09-01T00:00:00"), date and time("2019-08-17T00:00:00")) // False
before([1..4], 5) // True
before(1, 5) // True
```

#### after 函数
判断【参数1】是否在【参数2】之后，返回 bool

```
after(date and time("2023-09-01T00:00:00"), date and time("2019-08-17T00:00:00")) // True
after([1..4], 0) // True
after(1, 5) // False
```


#### includes 函数
判断【参数1】是否包含【参数2】，返回 bool

```
includes([1..4], 1) // True
includes([1..5], 6) // False
```


#### get or else 函数
如果【参数1】为 null，则返回【参数2】，否则返回【参数1】

```
get or else(null, 1) // 1
get or else(1, 2) // 1
```

#### is defined 函数
判断【参数】是否为 null，返回 bool

```
is defined(1) // True
is defined(null) // False
```


### 开发者自定义函数调用

开发者可以注册自定义函数并进行调用，注册方式请参考[README.md](../README.md)。

```
hello world(1, 2, 3) // 6
hello world(a:1, b:2) // 3
```
