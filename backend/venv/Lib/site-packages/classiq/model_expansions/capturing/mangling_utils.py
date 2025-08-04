import re
from typing import Optional

from classiq.interface.generator.compiler_keywords import CAPTURE_SUFFIX
from classiq.interface.model.handle_binding import HANDLE_ID_SEPARATOR, HandleBinding

IDENTIFIER_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_]*"
CAPTURE_PATTERN = re.compile(
    rf"({IDENTIFIER_PATTERN}){CAPTURE_SUFFIX}{IDENTIFIER_PATTERN}__\d*"
)
ARRAY_CAST_SUFFIX = HANDLE_ID_SEPARATOR + "array_cast"


def mangle_captured_var_name(
    var_name: str, function_name: str, function_depth: int
) -> str:
    return f"{var_name}{CAPTURE_SUFFIX}{function_name}__{function_depth}"


def _match_capture_pattern(name: str) -> Optional[re.Match[str]]:
    return re.match(CAPTURE_PATTERN, name)


def is_captured_var_name(name: str) -> bool:
    return _match_capture_pattern(name) is not None


def demangle_capture_name(name: str) -> str:
    match = _match_capture_pattern(name)
    return match.group(1) if match else name


def demangle_handle(handle: HandleBinding) -> HandleBinding:
    demangled_name = demangle_name(handle.name)
    return handle.rename(demangled_name)


def demangle_name(name: str) -> str:
    if HANDLE_ID_SEPARATOR not in name:
        return name
    if ARRAY_CAST_SUFFIX in name:
        return name.split(ARRAY_CAST_SUFFIX)[0]
    name = re.sub(r"([^_])_\d+$", r"\1", name)
    name_parts = name.split(HANDLE_ID_SEPARATOR)
    new_name_parts = [name_parts[0]]
    for part in name_parts[1:]:
        if re.fullmatch(r"\d+", part):
            new_name_parts.append(f"[{part}]")
        elif re.fullmatch(r"\d+_\d+", part):
            part_left, part_right = part.split("_")
            new_name_parts.append(f"[{part_left}:{part_right}]")
        else:
            new_name_parts.append(f".{part}")
    new_name_parts = list(map(demangle_capture_name, new_name_parts))
    new_name = "".join(new_name_parts)
    return new_name
