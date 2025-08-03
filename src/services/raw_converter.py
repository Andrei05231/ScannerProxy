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
            (0x50, 0x50): 'pdf',  # ASCII 'PP' (PDF format)
            (0x50, 0x44): 'pdf',  # ASCII 'PD' (alternative PDF marker)
            (0x50, 0x46): 'pdf'   # ASCII 'PF' (alternative PDF marker)
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
        header_width = struct.unpack('<H', header[12:14])[0]  # This might be row data width, not pixel width
        
        # Interpret header values
        scan_type = self.scan_type_map.get(scan_type_byte, f'unknown_0x{scan_type_byte:02X}')
        quality = self.quality_map.get(quality_byte, f'unknown_0x{quality_byte:02X}')
        format_type = self.format_map.get((format_byte1, format_byte2), 
                                        f'unknown_0x{format_byte1:02X}{format_byte2:02X}')
        
        # Determine actual image dimensions based on scan type
        if scan_type == 'color':
            # For color images, header_width is the row data width (RGB bytes)
            # Actual image width = header_width / 3
            if header_width % 3 == 0:
                width = header_width // 3  # Pixel width
                bytes_per_pixel = 3  # RGB
                row_data_width = header_width  # Byte width
            else:
                # Fallback if not divisible by 3
                width = header_width
                bytes_per_pixel = 1
                row_data_width = header_width
        else:
            # For B&W and grayscale, header_width is the actual pixel width
            width = header_width
            bytes_per_pixel = 1
            row_data_width = header_width
            
        # Analyze file structure to find height
        file_size = file_path.stat().st_size
        header_size = 16  # Fixed header size
            
        # Calculate expected row structure
        # Each row: pixel_data + EOL_marker(2 bytes) + padding(2 bytes)
        expected_pixel_data_per_row = row_data_width  # Use row_data_width instead of width * bytes_per_pixel
        expected_row_size = expected_pixel_data_per_row + 4  # +4 for EOL + padding
        
        # Calculate height based on file structure
        data_size = file_size - header_size
        if expected_row_size > 0:
            height = data_size // expected_row_size
            row_size = expected_row_size
            pixel_data_per_row = expected_pixel_data_per_row
        else:
            height = 0
            row_size = 0
            pixel_data_per_row = 0
            
        # Verify our calculation by checking actual EOL markers at expected positions
        eol_marker = struct.pack('<H', header_width)  # Use header_width for EOL marker
        verified_height = 0
        
        if height > 0:
            with open(file_path, 'rb') as f:
                f.seek(header_size)  # Skip header
                
                for row in range(min(height, 10)):  # Check first 10 rows for verification
                    # Skip to expected EOL position
                    f.seek(header_size + row * row_size + pixel_data_per_row)
                    
                    # Read potential EOL marker
                    potential_eol = f.read(2)
                    if potential_eol == eol_marker:
                        verified_height += 1
                    else:
                        # If EOL doesn't match, our calculation might be wrong
                        self.logger.warning(f"EOL verification failed at row {row}: expected {eol_marker.hex()}, got {potential_eol.hex()}")
                        break
                        
            # If verification failed for early rows, fall back to counting all EOL markers
            if verified_height < min(height, 10) and verified_height < 5:
                self.logger.warning("Row structure verification failed, falling back to EOL marker counting")
                with open(file_path, 'rb') as f:
                    data = f.read()
                height = data.count(eol_marker)
                if height > 0:
                    data_size = file_size - header_size
                    row_size = data_size // height
                    pixel_data_per_row = row_size - 4
            
        metadata = {
            'scan_type': scan_type,
            'quality': quality,
            'format_type': format_type,
            'width': width,  # Actual image width in pixels
            'height': height,
            'header_width': header_width,  # Width value from header (row data width for color)
            'row_data_width': row_data_width,  # Actual row data width in bytes
            'file_size': file_size,
            'header_size': header_size,
            'row_size': row_size,
            'pixel_data_per_row': pixel_data_per_row,
            'bytes_per_pixel': bytes_per_pixel,
            'estimated_bits_per_pixel': (pixel_data_per_row * 8 / row_data_width) if row_data_width > 0 else 0
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
            scan_type = metadata['scan_type']
            
            image_data = []
            eol_marker = struct.pack('<H', width)
            
            for row in range(height):
                # Read entire row of data
                row_data = f.read(row_size)
                if len(row_data) < row_size:
                    self.logger.warning(f"Incomplete row {row}: got {len(row_data)} bytes, expected {row_size}")
                    break
                    
                # Extract pixel data from the beginning of the row
                pixel_data = row_data[:pixel_data_per_row]
                
                # Verify EOL marker at the expected position (after pixel data)
                eol_position = pixel_data_per_row
                actual_eol = row_data[eol_position:eol_position+2]
                
                if actual_eol != eol_marker:
                    self.logger.warning(f"EOL marker mismatch in row {row}: expected {eol_marker.hex()} at position {eol_position}, got {actual_eol.hex()}")
                    # Continue processing anyway, but log the issue
                
                # Convert pixel data based on scan type
                if scan_type == 'color' and len(pixel_data) >= width * 3:
                    # For color images, we have RGB data (3 bytes per pixel)
                    # Reshape to (width, 3) for RGB channels
                    rgb_data = np.frombuffer(pixel_data[:width * 3], dtype=np.uint8)
                    rgb_row = rgb_data.reshape((width, 3))
                    image_data.append(rgb_row)
                elif len(pixel_data) >= width:
                    # For B&W or grayscale (1 byte per pixel)
                    row_pixels = list(pixel_data[:width])
                    image_data.append(row_pixels)
                else:
                    expected_bytes = width * 3 if scan_type == 'color' else width
                    self.logger.warning(f"Insufficient pixel data in row {row}: got {len(pixel_data)} bytes, expected at least {expected_bytes}")
                    break
            
            # Convert to numpy array
            if image_data:
                if scan_type == 'color':
                    # For color images, stack the RGB rows
                    image_array = np.array(image_data, dtype=np.uint8)
                    self.logger.info(f"Extracted RGB image array shape: {image_array.shape} for {scan_type} image")
                else:
                    # For B&W and grayscale images
                    image_array = np.array(image_data, dtype=np.uint8)
                    self.logger.info(f"Extracted grayscale image array shape: {image_array.shape} for {scan_type} image")
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
            # For black & white, apply thresholding
            threshold = 128
            image_array = np.where(image_array > threshold, 255, 0).astype(np.uint8)
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'grayscale':
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'color':
            # For color images, we now have proper RGB data
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # RGB image (height, width, 3)
                pil_image = Image.fromarray(image_array, mode='RGB')
                self.logger.info("Color image converted as RGB")
            else:
                # Fallback to grayscale if color processing failed
                self.logger.warning("Color image processing failed, converting as grayscale")
                pil_image = Image.fromarray(image_array, mode='L')
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
            # For color images, we now have proper RGB data
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # RGB image (height, width, 3)
                pil_image = Image.fromarray(image_array, mode='RGB')
                self.logger.info("Color image converted as RGB")
            else:
                # Fallback to grayscale if color processing failed
                self.logger.warning("Color image processing failed, converting as grayscale")
                pil_image = Image.fromarray(image_array, mode='L')
        else:
            pil_image = Image.fromarray(image_array, mode='L')
            
        # Save as PNG
        pil_image.save(output_path, 'PNG', optimize=True)
        
        self.logger.info(f"Converted {raw_file_path} to {output_path}")
        return output_path
    
    def convert_to_pdf(self, raw_file_path: Path, output_path: Optional[Path] = None, 
                      quality: int = 95) -> Path:
        """
        Convert raw file to PDF format.
        
        Args:
            raw_file_path: Path to the input raw file
            output_path: Path for output PDF file (optional)
            quality: JPG quality for PDF compression (1-100)
            
        Returns:
            Path to the created PDF file
        """
        # Extract image data
        image_array, metadata = self.extract_image_data(raw_file_path)
        
        # Determine output path
        if output_path is None:
            output_path = raw_file_path.with_suffix('.pdf')
            
        # Create PIL Image
        if metadata['scan_type'] == 'black_white':
            threshold = 128
            image_array = np.where(image_array > threshold, 255, 0).astype(np.uint8)
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'grayscale':
            pil_image = Image.fromarray(image_array, mode='L')
        elif metadata['scan_type'] == 'color':
            # For color images, we now have proper RGB data
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # RGB image (height, width, 3)
                pil_image = Image.fromarray(image_array, mode='RGB')
                self.logger.info("Color image converted as RGB")
            else:
                # Fallback to grayscale if color processing failed
                self.logger.warning("Color image processing failed, converting as grayscale")
                pil_image = Image.fromarray(image_array, mode='L')
        else:
            pil_image = Image.fromarray(image_array, mode='L')
            
        # Save as PDF
        # PIL can save images directly as PDF
        if pil_image.mode == 'RGB':
            # For RGB images, save directly
            pil_image.save(output_path, 'PDF', resolution=300.0, optimize=True)
        else:
            # For grayscale/B&W images, we can optionally compress them
            pil_image.save(output_path, 'PDF', resolution=300.0, optimize=True)
        
        self.logger.info(f"Converted {raw_file_path} to {output_path}")
        return output_path


def convert_raw_file(input_path: str, output_path: Optional[str] = None, 
                    output_format: str = 'jpg', quality: int = 95) -> str:
    """
    Convenience function to convert a raw file to standard image format.
    
    Args:
        input_path: Path to input raw file
        output_path: Path for output file (optional)
        output_format: Output format ('jpg', 'png', or 'pdf')
        quality: JPG/PDF quality if applicable (1-100)
        
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
    elif output_format.lower() == 'pdf':
        result_path = converter.convert_to_pdf(raw_path, out_path, quality)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
        
    return str(result_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python raw_converter.py <input_raw_file> [output_file] [format] [quality]")
        print("Supported formats: jpg, png, pdf")
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
