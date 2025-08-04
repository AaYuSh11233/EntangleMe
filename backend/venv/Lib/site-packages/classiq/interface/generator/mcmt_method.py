from classiq.interface.enum_utils import StrEnum


class McmtMethod(StrEnum):
    vchain = "vchain"
    mcxvchain = "mcxvchain"
    recursive = "recursive"
    standard = "standard"
    standard_no_neg_ctrl = "standard_no_neg_ctrl"
