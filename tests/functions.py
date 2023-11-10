# -*- coding: utf-8 -*-
from bkflow_feel.utils import BaseFEELInvocation, InvocationInputsModel


def func_without_params():
    return "Without params"


def func_with_params(a, b, c):
    return "With params: {}, {}, {}".format(a, b, c)


def func_with_named_params(a, b, c):
    return "With named params: {}, {}, {}".format(a, b, c)


class HelloWorldFunc(BaseFEELInvocation):
    class Meta:
        func_name = "hello world"

    def invoke(self, *args, **kwargs):
        return "Hello world"


class HelloWorldWithParamsFunc(BaseFEELInvocation):
    class Meta:
        func_name = "hello world with params"

    def invoke(self, a, b, c=2, *args, **kwargs):
        return {"a": a, "b": b, "c": c, "args": args, "kwargs": kwargs}


class FuncWithInputsValidation(BaseFEELInvocation):
    class Meta:
        func_name = "func with inputs validation"

    class Inputs(InvocationInputsModel):
        a: int
        b: int
        c: int
        d = 20

        class Meta:
            ordering = ["a", "b", "c", "d"]

    def invoke(self, a, b, *args, **kwargs):
        return {"a": a, "b": b, "args": args, "kwargs": kwargs}
