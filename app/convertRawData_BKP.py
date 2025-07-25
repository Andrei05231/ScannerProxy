import sys
import struct
import numpy as np
from PIL import Image
from datetime import datetime
import os

fileDestination = os.environ['DESTINATION']
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

filePath = f'/srv/scans/{fileDestination}/converted_{timestamp}.png'

if len(sys.argv) < 2:
    print("Usage: python convertRawData.py <input_file>")
    sys.exit(1)

file = sys.argv[1]

#file = "scan.raw"
drift = 2  # adjust drift as needed

with open(file, "rb") as f:
    header = f.read(16)
    if header[:4] != b'R2PP':
        raise ValueError("Invalid header: Missing R2PP marker.")

    line_size_bytes = struct.unpack("<I", header[12:16])[0]
    width = line_size_bytes // 2  # 2 bytes per pixel, 16-bit grayscale

    data = f.read()

pixels = np.frombuffer(data, dtype=np.uint16)
pixel_count = pixels.size

height = pixel_count // width
cropped_len = height * width
pixels = pixels[:cropped_len]

img2d = pixels.reshape((height, width))

# Apply drift correction
corrected_img = np.zeros_like(img2d)
for r in range(height):
    offset = (r * drift) % width
    corrected_img[r] = np.roll(img2d[r], -offset)

def to_8bit(arr):
    norm = (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)
    return (norm * 255).astype(np.uint8)

img8 = to_8bit(corrected_img)
image = Image.fromarray(img8, mode='L')

scale_factor = 1.4  # 1.5 times taller, adjust as needed
new_height = int(height * scale_factor)

# Resize the image
taller_image = image.resize((width, new_height), resample=Image.BICUBIC)

taller_image.save(filePath)

print(f"Image dimensions: {width} x {height}")

