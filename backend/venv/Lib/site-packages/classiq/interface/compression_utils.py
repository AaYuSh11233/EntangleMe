import base64
from collections.abc import Sequence
from typing import Union

import zstandard as zstd
from pydantic import BaseModel
from pydantic_core import from_json, to_json


def compress_pydantic(obj: Union[BaseModel, Sequence[BaseModel]]) -> bytes:
    json_data = to_json(obj)
    compressed_data = _compress(json_data, level=22)  # max compression level
    return compressed_data


def decompress(compressed_data: bytes) -> Union[dict, list[dict]]:
    decompressed_data = _decompress(compressed_data)
    return from_json(decompressed_data)


def _compress(data: bytes, level: int) -> bytes:
    compressor = zstd.ZstdCompressor(level=level)
    compressed_data = compressor.compress(data)
    b64_compressed_data = base64.b64encode(compressed_data)
    return b64_compressed_data


def _decompress(data: bytes) -> bytes:
    compressed_data = base64.b64decode(data)
    decompressor = zstd.ZstdDecompressor()
    return decompressor.decompress(compressed_data)
