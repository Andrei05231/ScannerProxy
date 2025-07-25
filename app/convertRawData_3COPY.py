import sys
import struct
import numpy as np
from PIL import Image
from datetime import datetime
import os

# === Config ===
DRIFT = 2
SCALE_FACTOR = 1.4
DEST_DIR = os.environ.get('DESTINATION', 'default')

# === Output Path ===
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = f'/srv/scans/{DEST_DIR}/converted_{timestamp}.png'

if len(sys.argv) < 2:
    print("Usage: python convertRawData.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]

# === Read file ===
with open(input_file, "rb") as f:
    header = f.read(16)
    if header[:4] != b'R2PP':
        raise ValueError("Invalid header: Missing R2PP marker.")

    line_size_bytes = struct.unpack("<I", header[12:16])[0]
    width = line_size_bytes // 2  # ❗FIXED width, even though data is RGB
    raw = f.read()

# === Interpret as packed RGB ===
data = np.frombuffer(raw, dtype=np.uint16)

bytes_per_pixel = 3 * 2  # R, G, B × 16-bit
pixels_per_row = width
values_per_row = pixels_per_row * 3  # 3 values (R, G, B) per pixel

total_rows = data.size // values_per_row
usable_data_len = total_rows * values_per_row
data = data[:usable_data_len]

# === Reshape into (height, width, 3) ===
image_data = data.reshape((total_rows, width, 3))

# === Apply drift correction ===
def correct_drift_rgb(img):
    corrected = np.zeros_like(img)
    for r in range(img.shape[0]):
        offset = (r * DRIFT) % img.shape[1]
        corrected[r] = np.roll(img[r], -offset, axis=0)
    return corrected

corrected = correct_drift_rgb(image_data)

# === Normalize 16-bit to 8-bit ===
def to_8bit(arr):
    arr = arr.astype(np.float32)
    norm = (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)
    return (norm * 255).astype(np.uint8)

rgb8 = to_8bit(corrected)

# === Convert to image and resize ===
img = Image.fromarray(rgb8, mode='RGB')
resized = img.resize((width, int(total_rows * SCALE_FACTOR)), Image.BICUBIC)
resized.save(output_path)

print(f"✅ Saved image: {output_path}")
print(f"📏 Dimensions: {width} x {total_rows}")

