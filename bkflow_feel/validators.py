# -*- coding: utf-8 -*-
import abc

from .exceptions import ValidationError


class ValidationResult:
    def __init__(self, result: bool, err_msg: str = None, *args, **kwargs):
        self.result = result
        self.err_msg = err_msg


class Validator(metaclass=abc.ABCMeta):
    def __call__(self, *args, **kwargs):
        validation_result = self.validate(*args, **kwargs)
        if not validation_result.result:
            raise ValidationError(validation_result.err_msg)
        return validation_result

    @abc.abstractmethod
    def validate(self, *args, **kwargs) -> ValidationResult:
        pass


class DummyValidator(Validator):
    def validate(self, *args, **kwargs):
        pass


class ListsLengthValidator(Validator):
    def validate(self, lists, *args, **kwargs):
        if not lists or all(len(alist) == len(lists[0]) for alist in lists):
            return ValidationResult(True)
        return ValidationResult(False, "lists length not equal")


class BinaryOperationValidator(Validator):
    def validate(self, left_item, right_item, instance_type=None, *args, **kwargs) -> ValidationResult:
        if not isinstance(left_item, type(right_item)):
            return ValidationResult(
                False, f"Type of both operators must be same, get {type(left_item)} and {type(right_item)}",
            )
        if instance_type is not None and not isinstance(left_item, instance_type):
            return ValidationResult(
                False, f"Type of both operators must be {instance_type}, get {type(left_item)} and {type(right_item)}",
            )
        return ValidationResult(True)
