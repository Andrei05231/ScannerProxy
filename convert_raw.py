#!/usr/bin/env python3
"""
Simple raw file converter script.

Usage:
    python convert_raw.py <input_raw_file> [output_file]

Examples:
    python convert_raw.py files/black_white_test_v1.raw
    python convert_raw.py files/black_white_test_v1.raw files/my_output.jpg
    python convert_raw.py files/color_jpg.raw files/color_output.pdf
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / 'src'))

from src.services.raw_converter import RawFileConverter


def main():
    """Main function to convert raw file to JPG."""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a raw file to convert")
        print()
        print("Usage:")
        print(f"    python {Path(__file__).name} <input_raw_file> [output_file]")
        print()
        print("Examples:")
        print(f"    python {Path(__file__).name} files/black_white_test_v1.raw")
        print(f"    python {Path(__file__).name} files/black_white_test_v1.raw files/my_output.jpg")
        print(f"    python {Path(__file__).name} files/color_jpg.raw files/color_output.pdf")
        print()
        print("Supported output formats: .jpg, .png, .pdf")
        sys.exit(1)
    
    # Get input file
    input_file = Path(sys.argv[1])
    
    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Get output file (optional)
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        # Generate output filename based on input and format from header
        metadata = RawFileConverter().analyze_raw_file(input_file)
        if metadata['format_type'] == 'pdf':
            output_file = input_file.with_suffix('.pdf')
        else:
            # Default to JPG for unknown or JPG formats
            output_file = input_file.with_suffix('.jpg')
    
    print(f"🔄 Converting: {input_file}")
    print(f"📁 Output to: {output_file}")
    print()
    
    try:
        # Create converter
        converter = RawFileConverter()
        
        # Analyze the file first
        print("📊 Analyzing raw file...")
        metadata = converter.analyze_raw_file(input_file)
        
        print(f"   Type: {metadata['scan_type']}")
        print(f"   Quality: {metadata['quality']}")
        print(f"   Format: {metadata['format_type']}")
        print(f"   Dimensions: {metadata['width']} x {metadata['height']}")
        print(f"   File size: {metadata['file_size']:,} bytes")
        print()
        
        # Convert to appropriate format based on file header or output extension
        output_format = output_file.suffix.lower().lstrip('.')
        if output_format not in ['jpg', 'jpeg', 'png', 'pdf']:
            # If no valid extension, use format from header
            if metadata['format_type'] == 'pdf':
                output_format = 'pdf'
            else:
                output_format = 'jpg'  # Default
                
        print(f"🖼️  Converting to {output_format.upper()}...")
        
        if output_format in ['jpg', 'jpeg']:
            result_path = converter.convert_to_jpg(input_file, output_file, quality=95)
        elif output_format == 'png':
            result_path = converter.convert_to_png(input_file, output_file)
        elif output_format == 'pdf':
            result_path = converter.convert_to_pdf(input_file, output_file, quality=95)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
        
        # Show result
        output_size = result_path.stat().st_size
        print(f"✅ Success! Converted to: {result_path}")
        print(f"📏 Output size: {output_size:,} bytes")
        
        # Calculate compression ratio
        compression_ratio = (metadata['file_size'] - output_size) / metadata['file_size'] * 100
        print(f"📉 Compression: {compression_ratio:.1f}% smaller than raw file")
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Change to script directory for relative paths
    os.chdir(script_dir)
    main()
