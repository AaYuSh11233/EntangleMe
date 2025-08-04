import sys
from typing import Any

if sys.version_info[0:2] >= (3, 10):
    zip_strict = zip
else:

    def zip_strict(*iterables: Any, strict: bool = False) -> zip:
        return zip(*iterables)
