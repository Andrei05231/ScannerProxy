import sys
import struct
import os
import numpy as np
from PIL import Image
from datetime import datetime
from pathlib import Path
import humanize

# Destination path setup with better environment variable handling
destination = Path.cwd() / "scans"  # Default fallback
if "DESTINATION" in os.environ:
    destination = Path('/srv/scans') / os.environ['DESTINATION']

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
file_path = destination / f'converted_{timestamp}.png'

# Input check
if len(sys.argv) < 2:
    print("Usage: python convert_raw_data.py <input_file>")
    sys.exit(1)

input_file = Path(sys.argv[1])

# Validate input file
if not input_file.exists():
    print(f"Error: Input file '{input_file}' does not exist")
    sys.exit(1)

# Create output directory
file_path.parent.mkdir(parents=True, exist_ok=True)

# Drift parameter (adjust if necessary)
drift = 2

# Read file with better error handling
try:
    with input_file.open("rb") as f:
        header = f.read(16)
        if header[:4] != b'R2PP':
            raise ValueError("Invalid header: Missing R2PP marker.")

        line_size_bytes = struct.unpack("<I", header[12:16])[0]
        print(f"Line size (from header): {line_size_bytes} bytes")
        print(f"Input file size: {humanize.naturalsize(input_file.stat().st_size)}")

        data = f.read()
except IOError as e:
    print(f"Error reading input file: {e}")
    sys.exit(1)

pixels = np.frombuffer(data, dtype=np.uint16)

# Try to detect image format
image = None
mode = 'unknown'

def to_8bit(arr):
    norm = (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)
    return (norm * 255).astype(np.uint8)

if line_size_bytes % 6 == 0:
    # Likely 16-bit RGB interleaved
    mode = 'color'
    width = line_size_bytes // 6
    total_pixels = pixels.size
    expected_total = width * 3

    height = total_pixels // expected_total
    print(f"Detected color image: {width} x {height}")

    # Trim extra
    pixels = pixels[:height * width * 3]
    rgb = pixels.reshape((height, width, 3))  # shape: (H, W, [R, G, B])

    # Drift correction on each channel
    corrected_rgb = np.zeros_like(rgb)
    for r in range(height):
        offset = (r * drift) % width
        corrected_rgb[r] = np.roll(rgb[r], -offset, axis=0)

    # Convert to 8-bit per channel
    rgb8 = np.zeros_like(corrected_rgb, dtype=np.uint8)
    for c in range(3):
        rgb8[:, :, c] = to_8bit(corrected_rgb[:, :, c])

    image = Image.fromarray(rgb8, mode='RGB')

elif line_size_bytes % 2 == 0:
    # Assume grayscale 16-bit
    mode = 'grayscale'
    width = line_size_bytes // 2
    pixel_count = pixels.size
    height = pixel_count // width
    print(f"Detected grayscale image: {width} x {height}")

    pixels = pixels[:width * height]
    img2d = pixels.reshape((height, width))

    # Drift correction
    corrected_img = np.zeros_like(img2d)
    for r in range(height):
        offset = (r * drift) % width
        corrected_img[r] = np.roll(img2d[r], -offset)

    img8 = to_8bit(corrected_img)
    image = Image.fromarray(img8, mode='L')

else:
    raise ValueError("Unsupported or unknown line size format.")

# Resize vertically
scale_factor = 1.4
new_height = int(height * scale_factor)
image = image.resize((width, new_height), resample=Image.BICUBIC)

# Save output
image.save(file_path)
print(f"Saved {mode} image to: {file_path}")
print(f"Final image dimensions: {width} x {new_height}")
print(f"Output file size: {humanize.naturalsize(file_path.stat().st_size)}")

