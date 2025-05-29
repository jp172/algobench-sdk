import logging
from algobench.decorator import algorithm

__all__ = ["algorithm"]

logging.getLogger("algobench").addHandler(logging.NullHandler())
