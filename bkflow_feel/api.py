# -*- coding: utf-8 -*-
import logging

from . import parser as default_parser
from . import transformer as default_transformer
from .exceptions import ValidationError
from .parsers import Expression

logger = logging.getLogger(__name__)


def parse_expression(
    expression, context=None, raise_exception=True, parser=default_parser, transformer=default_transformer,
):
    parse_tree = parser.parse(expression)
    logger.debug(parse_tree)
    ast = transformer.transform(parse_tree)
    logger.debug(ast)
    if not isinstance(ast, Expression):
        msg = f"Invalid FEEL expression: {expression}, ast: {ast}"
        logger.error(msg)
        if raise_exception:
            raise ValueError(msg)
        return None
    try:
        result = ast.evaluate(context or {})
    except ValidationError as e:
        logger.exception(f"evaluate expression error: {e}")
        if raise_exception:
            raise e
        return None
    except Exception as e:
        logger.exception(f"evaluate expression error: {e}")
        if raise_exception:
            raise e
        return None
    return result
