# -*- coding: utf-8 -*-
import abc
import importlib
import logging
from typing import Callable

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic import validate_arguments

from bkflow_feel.exceptions import ValidationError

logger = logging.getLogger(__name__)


class FEELFunctionsManager:
    __hub = {}

    @classmethod
    def register_invocation_cls(cls, invocation_cls):
        func_name = invocation_cls.Meta.func_name
        existed_invocation_cls = cls.__hub.get(func_name)
        if existed_invocation_cls:
            raise RuntimeError(
                "func register error, {}'s func_name {} conflict with {}".format(
                    existed_invocation_cls, func_name, invocation_cls
                )
            )

        cls.__hub[func_name] = invocation_cls

    @classmethod
    def register_funcs(cls, func_dict):
        for func_name, func_path in func_dict.items():
            if not isinstance(func_name, str):
                raise ValueError(f"func_name {func_name} should be string")
            if func_name in cls.__hub:
                raise ValueError(
                    "func register error, {}'s func_name {} conflict with {}".format(
                        func_path, func_name, cls.__hub[func_name]
                    )
                )
            cls.__hub[func_name] = func_path

    @classmethod
    def clear(cls):
        cls.__hub = {}

    @classmethod
    def all_funcs(cls):
        funcs = {}
        for version, invocation_cls in cls.__hub.items():
            funcs[version] = invocation_cls
        return funcs

    @classmethod
    def get_func(cls, func_name) -> Callable:
        func_obj = cls.__hub.get(func_name)
        if not func_obj:
            raise ValueError("func object {} not found".format(func_name))

        if isinstance(func_obj, FEELInvocationMeta):
            return func_obj()
        else:
            module_path, func_name = str(func_obj).rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            return func

    @classmethod
    def func_call(cls, func_name, *args, **kwargs):
        func = cls.get_func(func_name)
        return func(*args, **kwargs)


class FEELInvocationMeta(type):
    """
    Metaclass for FEEL function invocation
    """

    def __new__(cls, name, bases, dct):
        # ensure initialization is only performed for subclasses of Plugin
        parents = [b for b in bases if isinstance(b, FEELInvocationMeta)]
        if not parents:
            return super().__new__(cls, name, bases, dct)

        new_cls = super().__new__(cls, name, bases, dct)

        # meta validation
        meta_obj = getattr(new_cls, "Meta", None)
        if not meta_obj:
            raise AttributeError("Meta class is required")

        func_name = getattr(meta_obj, "func_name", None)
        if not func_name:
            raise AttributeError("func_name is required in Meta")

        desc = getattr(meta_obj, "desc", None)
        if desc is not None and not isinstance(desc, str):
            raise AttributeError("desc in Meta should be str")

        # register func
        FEELFunctionsManager.register_invocation_cls(new_cls)

        return new_cls


class InvocationInputsModel(BaseModel):
    """
    Model for inputs of invocation
    """

    pass


class BaseFEELInvocation(metaclass=FEELInvocationMeta):
    """
    Base class for FEEL function invocation
    """

    class Inputs(InvocationInputsModel):
        """
        Inputs class for FEEL function invocation
        """

        pass

    @validate_arguments
    def __call__(self, *args, **kwargs):

        # 输入参数校验, 仅可能是 args 或 kwargs 之一
        try:
            params = {}
            if args:
                inputs_meta = getattr(self.Inputs, "Meta", None)
                inputs_ordering = getattr(inputs_meta, "ordering", None)
                if isinstance(inputs_ordering, list):
                    if len(args) > len(inputs_ordering):
                        raise ValidationError(f"Too many arguments for inputs: {args}")
                    params = {k: v for k, v in zip(inputs_ordering, args)}
            elif kwargs:
                params = kwargs

            if params:
                self.Inputs(**params)
        except PydanticValidationError as e:
            raise ValidationError(e)

        return self.invoke(*args, **kwargs)

    @abc.abstractmethod
    def invoke(self, *args, **kwargs):
        raise NotImplementedError()
