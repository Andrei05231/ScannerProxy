"""
Raw file converter for scanner proxy files.

This module handles conversion of custom raw scanner files to standard image formats (JPG, PNG).
The raw format uses a custom header structure and includes end-of-line markers.
"""

import logging
import struct
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import numpy as np


class RawFileConverter:
    """
    Converter for custom raw scanner files to standard image formats.
    
    Raw file format structure:
    - Byte 0: Scan type (B=black/white, G=grayscale, R=color)
    - Byte 1: Quality indicator (ASCII '2'=50=standard, '3'=51=medium, '6'=54=high)
    - Byte 2: Format type (ASCII 'J'=JPG, 'P'=PDF first part)
    - Byte 3: Format type continuation ('P' for JPG)
    - Bytes 4-7: Reserved/padding (0x00000000)
    - Bytes 8-11: Unknown metadata
    - Bytes 12-13: Width (little-endian 16-bit)
    - Bytes 14-15: Reserved/padding
    - Bytes 16+: Image data with EOL markers
    
    Image data structure:
    - Each row: [pixel_data] + [width_as_eol_marker] + [padding]
    - EOL marker: width value (2 bytes, little-endian)
    - Total row size: width + 4 bytes (2 for EOL + 2 for padding)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Quality mappings
        self.quality_map = {
            0x32: 'standard',  # ASCII '2'
            0x33: 'medium',    # ASCII '3'
            0x36: 'high'       # ASCII '6'
        }
        
        # Scan type mappings
        self.scan_type_map = {
            0x42: 'black_white',  # ASCII 'B'
            0x47: 'grayscale',    # ASCII 'G'
            0x52: 'color'         # ASCII 'R'
        }
        
        # Format mappings
        self.format_map = {
            (0x4A, 0x50): 'jpg',  # ASCII 'JP'
            (0x50, 0x44): 'pdf'   # ASCII 'PD' (assumption)
        }
    
    def analyze_raw_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a raw file and extract metadata from its header.
        
        Args:
            file_path: Path to the raw file
            
        Returns:
            Dictionary containing file metadata
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Raw file not found: {file_path}")
            
        with open(file_path, 'rb') as f:
            header = f.read(16)
            
        if len(header) < 16:
            raise ValueError(f"Invalid raw file: header too short ({len(header)} bytes)")
            
        # Parse header
        scan_type_byte = header[0]
        quality_byte = header[1]
        format_byte1 = header[2]
        format_byte2 = header[3]
        width = struct.unpack('<H', header[12:14])[0]  # Little-endian 16-bit
        
        # Interpret header values
        scan_type = self.scan_type_map.get(scan_type_byte, f'unknown_0x{scan_type_byte:02X}')
        quality = self.quality_map.get(quality_byte, f'unknown_0x{quality_byte:02X}')
        format_type = self.format_map.get((format_byte1, format_byte2), 
                                        f'unknown_0x{format_byte1:02X}{format_byte2:02X}')
        
        # Analyze file structure to find height
        file_size = file_path.stat().st_size
        
        # Find EOL markers to determine height
        with open(file_path, 'rb') as f:
            data = f.read()
            
        eol_marker = struct.pack('<H', width)  # Width as little-endian 16-bit
        height = data.count(eol_marker)
        
        # Calculate expected row size
        header_size = 16  # Fixed header size
        if height > 0:
            data_size = file_size - header_size
            row_size = data_size // height
            pixel_data_per_row = row_size - 4  # Subtract EOL marker + padding
        else:
            row_size = 0
            pixel_data_per_row = 0
            
        metadata = {
            'scan_type': scan_type,
            'quality': quality,
            'format_type': format_type,
            'width': width,
            'height': height,
            'file_size': file_size,
            'header_size': header_size,
            'row_size': row_size,
            'pixel_data_per_row': pixel_data_per_row,
            'estimated_bits_per_pixel': (pixel_data_per_row * 8 / width) if width > 0 else 0
        }
        
        self.logger.info(f"Raw file analysis: {metadata}")
        return metadata
    
    def extract_image_data(self, file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Extract image data from raw file.
        
        Args:
            file_path: Path to the raw file
            
        Returns:
            Tuple of (image_array, metadata)
        """
        metadata = self.analyze_raw_file(file_path)
        
        with open(file_path, 'rb') as f:
            # Skip header
            f.seek(metadata['header_size'])
            
            # Extract image data
            width = metadata['width']
            height = metadata['height']
            row_size = metadata['row_size']
            pixel_data_per_row = metadata['pixel_data_per_row']
            
            image_data = []
            
            for row in range(height):
                # Read one row of data
                row_data = f.read(row_size)
                if len(row_data) < row_size:
                    self.logger.warning(f"Incomplete row {row}: got {len(row_data)} bytes, expected {row_size}")
                    break
                    
                # Extract pixel data (exclude EOL marker and padding)
                pixel_data = row_data[:pixel_data_per_row]
                
                # Verify EOL marker
                eol_marker = row_data[pixel_data_per_row:pixel_data_per_row+2]
                expected_eol = struct.pack('<H', width)
                if eol_marker != expected_eol:
                    self.logger.warning(f"Unexpected EOL marker in row {row}: {eol_marker.hex()}")
                
                # Convert to pixel values (assuming 8-bit grayscale for now)
                if len(pixel_data) >= width:
                    row_pixels = list(pixel_data[:width])
                    image_data.append(row_pixels)
                else:
                    self.logger.warning(f"Insufficient pixel data in row {row}: {len(pixel_data)} bytes")
                    break
            
            # Convert to numpy array
            if image_data:
                image_array = np.array(image_data, dtype=np.uint8)
                self.logger.info(f"Extracted image array shape: {image_array.shape}")
            else:
                raise ValueError("No valid image data extracted")
                
        return image_array, metadata
    
    def convert_to_jpg(self, raw_file_path: Path, output_path: Optional[Path] = None, 
                      quality: int = 95) -> Path:
        """
        Convert raw file to JPG format.
        
        Args:
            raw_file_path: Path to the input raw file
            output_path: Path for output JPG file (optional)
            quality: JPG quality (1-100)
            
        Returns:
            Path to the created JPG file
        """
        # Extract image data
        image_array, metadata = self.extract_image_data(raw_file_path)
        
        # Determine output path
        if output_path is None:
            output_path = raw_file_path.with_suffix('.jpg')
            
        # Create PIL Image
        if metadata['scan_type'] == 'black_white':
            # For black & white, we might need to apply thresholding
            # Convert to pure black and white
            threshold = 128
            image_array = np.where(image_array > threshold, 255, 0).astype(np.uint8)
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'grayscale':
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'color':
            # For color images, we'd need to handle RGB data differently
            # This would require understanding how color data is stored
            pil_image = Image.fromarray(image_array, mode='L')  # Fallback to grayscale
            self.logger.warning("Color mode not fully implemented, converting as grayscale")
        else:
            pil_image = Image.fromarray(image_array, mode='L')
            
        # Save as JPG
        pil_image.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        self.logger.info(f"Converted {raw_file_path} to {output_path}")
        return output_path
    
    def convert_to_png(self, raw_file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Convert raw file to PNG format.
        
        Args:
            raw_file_path: Path to the input raw file
            output_path: Path for output PNG file (optional)
            
        Returns:
            Path to the created PNG file
        """
        # Extract image data
        image_array, metadata = self.extract_image_data(raw_file_path)
        
        # Determine output path
        if output_path is None:
            output_path = raw_file_path.with_suffix('.png')
            
        # Create PIL Image
        if metadata['scan_type'] == 'black_white':
            threshold = 128
            image_array = np.where(image_array > threshold, 255, 0).astype(np.uint8)
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'grayscale':
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'color':
            pil_image = Image.fromarray(image_array, mode='L')  # Fallback
            self.logger.warning("Color mode not fully implemented, converting as grayscale")
        else:
            pil_image = Image.fromarray(image_array, mode='L')
            
        # Save as PNG
        pil_image.save(output_path, 'PNG', optimize=True)
        
        self.logger.info(f"Converted {raw_file_path} to {output_path}")
        return output_path


def convert_raw_file(input_path: str, output_path: Optional[str] = None, 
                    output_format: str = 'jpg', quality: int = 95) -> str:
    """
    Convenience function to convert a raw file to standard image format.
    
    Args:
        input_path: Path to input raw file
        output_path: Path for output file (optional)
        output_format: Output format ('jpg' or 'png')
        quality: JPG quality if applicable (1-100)
        
    Returns:
        Path to the converted file
    """
    converter = RawFileConverter()
    raw_path = Path(input_path)
    
    if output_path:
        out_path = Path(output_path)
    else:
        out_path = None
        
    if output_format.lower() in ['jpg', 'jpeg']:
        result_path = converter.convert_to_jpg(raw_path, out_path, quality)
    elif output_format.lower() == 'png':
        result_path = converter.convert_to_png(raw_path, out_path)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
        
    return str(result_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python raw_converter.py <input_raw_file> [output_file] [format] [quality]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    format_type = sys.argv[3] if len(sys.argv) > 3 else 'jpg'
    quality = int(sys.argv[4]) if len(sys.argv) > 4 else 95
    
    try:
        result = convert_raw_file(input_file, output_file, format_type, quality)
        print(f"Successfully converted to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
