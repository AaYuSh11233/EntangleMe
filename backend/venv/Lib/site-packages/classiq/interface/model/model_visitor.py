from classiq.interface.debug_info.debug_info import DebugInfoCollection
from classiq.interface.generator.visitor import Transformer, Visitor


class ModelVisitor(Visitor):
    def visit_DebugInfoCollection(self, debug_info: DebugInfoCollection) -> None:
        return


class ModelTransformer(Transformer):
    def visit_DebugInfoCollection(
        self, debug_info: DebugInfoCollection
    ) -> DebugInfoCollection:
        return debug_info
