from typing import Any

from classiq.interface.ide.visual_model import Operation


class OperationRegistry:
    def __init__(self) -> None:
        self._operation_hash_to_op_id: dict[int, int] = {}
        self._id_to_operations: dict[int, Operation] = {}
        self._unique_op_counter = 0
        self._deduped_op_counter = 0

    def build_operation(self, **kwargs: Any) -> Operation:
        operation = Operation(**kwargs)
        return self._add_operation(operation)

    def _add_operation(self, op: Operation) -> Operation:
        """
        Adds an operation to the global dictionaries for operations.
        if operation already exist in the registry, it returns the existing operation.
        """
        op_hash = hash(op)
        if op_hash not in self._operation_hash_to_op_id:
            self._operation_hash_to_op_id[op_hash] = op.id
            self._id_to_operations[op.id] = op
            self._unique_op_counter += 1
        else:
            self._deduped_op_counter += 1
            op = self._id_to_operations[self._operation_hash_to_op_id[op_hash]]
        return op

    def get_operation_mapping(self) -> dict[int, Operation]:
        return self._id_to_operations

    def get_operations(self, op_ids: list[int]) -> list[Operation]:
        """
        Returns a list of operations based on their IDs.
        """
        return [self._id_to_operations[op_id] for op_id in op_ids]

    def get_unique_op_number(self) -> int:
        return self._unique_op_counter

    def get_deduped_op_number(self) -> int:
        return self._deduped_op_counter
