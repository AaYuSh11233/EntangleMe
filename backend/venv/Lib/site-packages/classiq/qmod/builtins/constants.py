from classiq.qmod.cparam import CBool
from classiq.qmod.qmod_constant import QConstant

SIGNED = QConstant("SIGNED", CBool, True)
UNSIGNED = QConstant("UNSIGNED", CBool, False)

__all__ = [
    "SIGNED",
    "UNSIGNED",
]
