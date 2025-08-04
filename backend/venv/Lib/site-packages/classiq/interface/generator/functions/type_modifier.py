from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqInternalExpansionError


class TypeModifier(StrEnum):
    Const = "const"
    Permutable = "permutable"
    Mutable = "mutable"
    Inferred = "inferred"

    @staticmethod
    def and_(first: "TypeModifier", second: "TypeModifier") -> "TypeModifier":
        if second is TypeModifier.Inferred:
            raise ClassiqInternalExpansionError
        if first is TypeModifier.Mutable or second is TypeModifier.Mutable:
            return TypeModifier.Mutable
        elif first is TypeModifier.Permutable or second is TypeModifier.Permutable:
            return TypeModifier.Permutable
        else:
            if first is not TypeModifier.Const and second is not TypeModifier.Const:
                raise ClassiqInternalExpansionError("Unexpected type modifiers")
            return TypeModifier.Const
