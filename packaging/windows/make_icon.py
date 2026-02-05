import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PNG_PATH = ROOT / "assets" / "DexKeeper_Bot_icon_256.png"
FALLBACK_PNG = ROOT / "assets" / "DexKeeper_Bot_icon.png"
ICO_PATH = ROOT / "assets" / "DexKeeper_Bot_icon.ico"

PNG_SIG = b"\x89PNG\r\n\x1a\n"

def read_png_size(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIG):
        raise ValueError("Not a PNG file")
    # IHDR chunk starts at byte 8: length(4) + type(4)
    # PNG signature 8 bytes, then IHDR length 4, type 4, then width/height 4+4
    if data[12:16] != b"IHDR":
        raise ValueError("Invalid PNG: missing IHDR")
    width = struct.unpack(">I", data[16:20])[0]
    height = struct.unpack(">I", data[20:24])[0]
    return width, height

def write_ico(png_bytes: bytes, width: int, height: int) -> None:
    # ICO header
    reserved = 0
    ico_type = 1
    count = 1
    header = struct.pack("<HHH", reserved, ico_type, count)

    # Directory entry
    w = 0 if width >= 256 else width
    h = 0 if height >= 256 else height
    color_count = 0
    reserved = 0
    planes = 1
    bit_count = 32
    bytes_in_res = len(png_bytes)
    image_offset = 6 + 16  # header + dir entry
    entry = struct.pack(
        "<BBBBHHII",
        w,
        h,
        color_count,
        reserved,
        planes,
        bit_count,
        bytes_in_res,
        image_offset,
    )

    ICO_PATH.write_bytes(header + entry + png_bytes)


def main():
    png_source = PNG_PATH if PNG_PATH.exists() else FALLBACK_PNG
    if not png_source.exists():
        raise SystemExit(f"Missing PNG icon: {PNG_PATH}")
    png_bytes = png_source.read_bytes()
    width, height = read_png_size(png_bytes)
    if width != height:
        raise SystemExit(f"Icon must be square, got {width}x{height}")
    if width > 256 or height > 256:
        raise SystemExit(f"Icon too large for ICO (max 256x256), got {width}x{height}")
    write_ico(png_bytes, width, height)
    print(f"Wrote {ICO_PATH}")

if __name__ == "__main__":
    main()
