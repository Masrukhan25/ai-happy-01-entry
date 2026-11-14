#!/usr/bin/env python3
"""ai-happy-01 entry: copy the bundled artwork to the output directory.

Standard library only. No network. Deterministic: the output is a
byte-for-byte copy of the bundled image, so repeated runs agree.
"""
import os
import shutil
import struct
import sys

MAX_BYTES = 1048576
MAX_DIM = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def _png_dimensions(data):
    if len(data) < 33 or data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file")
    if data[12:16] != b"IHDR":
        raise ValueError("PNG missing IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _jpeg_dimensions(data):
    if len(data) < 4 or data[:3] != JPEG_MAGIC:
        raise ValueError("not a JPEG file")
    pos = 2
    while pos + 9 <= len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if pos + 4 > len(data):
            break
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if pos + 9 > len(data):
                break
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    raise ValueError("JPEG SOF marker not found")


def _image_dimensions(data):
    if data[:8] == PNG_MAGIC:
        return _png_dimensions(data)
    if data[:3] == JPEG_MAGIC:
        return _jpeg_dimensions(data)
    raise ValueError("unsupported image format (need PNG or JPEG)")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = None
    for name in ("entry.png", "entry.jpg"):
        candidate = os.path.join(here, name)
        if os.path.isfile(candidate):
            source = candidate
            break
    if source is None:
        print("error: bundled image (entry.png or entry.jpg) not found", file=sys.stderr)
        return 1

    with open(source, "rb") as f:
        data = f.read()

    if len(data) > MAX_BYTES:
        print("error: bundled image exceeds 1048576 bytes", file=sys.stderr)
        return 1

    width, height = _image_dimensions(data)
    if width > MAX_DIM or height > MAX_DIM:
        print("error: image dimensions exceed 1024x1024", file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    with open(dest, "wb") as f:
        f.write(data)

    print("wrote %s (%d bytes, %dx%d)" % (dest, len(data), width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
