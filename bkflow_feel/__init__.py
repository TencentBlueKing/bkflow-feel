# -*- coding: utf-8 -*-
from lark import Lark

from .transformer import FEELTransformer

parser = Lark.open("FEEL.lark", rel_to=__file__, parser="lalr")
transformer = FEELTransformer()
