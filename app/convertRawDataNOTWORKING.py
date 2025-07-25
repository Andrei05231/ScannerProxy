import sys
import struct
import numpy as np
from PIL import Image, ImageEnhance
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

    # Get the ACTUAL width from header (as you mentioned)
    line_size_bytes = struct.unpack("<I", header[12:16])[0]
    width = line_size_bytes // 2  # Your original correct calculation
    print(f"DEBUG: Line size bytes: {line_size_bytes}, Calculated width: {width}")
    
    raw = f.read()

# Interpret data as unsigned 16-bit
data = np.frombuffer(raw, dtype=np.uint16)
print(f"DEBUG: Data range: {data.min()} to {data.max()}")

# Calculate expected structure
pixels_per_row = width
values_per_row = pixels_per_row * 3  # R,G,B components
total_rows = len(data) // values_per_row
data = data[:total_rows * values_per_row]  # Trim to complete rows

# Reshape to (height, width, 3)
image_data = data.reshape((total_rows, width, 3))

# === Improved Normalization ===
def balanced_normalize(arr):
    # Convert to float
    fimg = arr.astype(np.float32)
    
    # Calculate automatic black/white points
    black_point = np.percentile(fimg, 5)  # 5th percentile as black point
    white_point = np.percentile(fimg, 95)  # 95th percentile as white point
    
    print(f"DEBUG: Normalization - Black: {black_point}, White: {white_point}")
    
    # Linear stretch with clipping
    normalized = np.clip((fimg - black_point) / (white_point - black_point + 1e-9), 0, 1)
    
    # Apply gamma correction (1.8 for smoother tones)
    normalized = np.power(normalized, 1/1.8)
    
    return (normalized * 255).astype(np.uint8)

rgb8 = balanced_normalize(image_data)

# === Image Processing ===
img = Image.fromarray(rgb8, mode='RGB')

# Apply gentle contrast enhancement
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.2)  # 1.0 = original, >1.0 = more contrast

# Resize
new_height = int(total_rows * SCALE_FACTOR)
resized = img.resize((width, new_height), Image.LANCZOS)

# Save
os.makedirs(os.path.dirname(output_path), exist_ok=True)
resized.save(output_path)

print(f"✅ Saved image: {output_path}")
print(f"📏 Dimensions: {width}x{total_rows} (orig) → {width}x{new_height} (scaled)")
print(f"🌈 Value range: {data.min()}-{data.max()} (raw) → {rgb8.min()}-{rgb8.max()} (8-bit)")
