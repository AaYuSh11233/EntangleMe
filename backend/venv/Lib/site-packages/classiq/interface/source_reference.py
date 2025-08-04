import os
import re
from pathlib import Path
from typing import Optional

import pydantic

from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)


def _identify_ipynb_cell(file_name: str) -> bool:
    file_path = Path(file_name)
    base_file = file_path.name
    if re.fullmatch(r"\d*\.py", base_file) is None:
        return False
    parent_folder = file_path.parent
    return re.fullmatch(r"ipykernel_\d*", parent_folder.name) is not None


def _prepare_file_string(file_name: str) -> str:
    if _identify_ipynb_cell(file_name):
        return "ipynb cell "
    return f"file {os.path.basename(file_name)} "


class SourceReference(HashablePydanticBaseModel):
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    file_name: Optional[str] = pydantic.Field(default=None)

    def __str__(self) -> str:
        return f"{self.file_string()}{self.ref_inside_file()}"

    def file_string(self) -> str:
        return _prepare_file_string(self.file_name) if self.file_name else ""

    def ref_inside_file(self) -> str:
        start_character_string = (
            f" character {self.start_column + 1}" if self.start_column > 0 else ""
        )
        return f"line {self.start_line + 1}{start_character_string}"


class SourceReferencedError(pydantic.BaseModel):
    error: str
    source_ref: Optional[SourceReference] = None
    function: Optional[str] = None

    def __str__(self) -> str:
        source_referenced_error = (
            f"{self.error}\n\t\tat {self.source_ref}"
            if self.source_ref is not None
            else self.error
        )
        function_scoped_error = (
            f"{source_referenced_error} in function {self.function}"
            if self.function is not None
            else source_referenced_error
        )
        return function_scoped_error
