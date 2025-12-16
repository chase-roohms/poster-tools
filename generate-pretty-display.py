#!/usr/bin/env python3
"""
Generate a pretty display with a collection poster (full height) on the left
and parent posters (auto generated dimensions) on the right.

Poster Naming Scheme:
- Collection posters should have filenames ending with "Collection" or "Productions" (e.g., "Pixar Collection.png").
- Parent posters should be named as "<Show or Movie Name> (Year)" (e.g., "Wacky Races (1968).png").
- Season or specials posters (e.g., "Show Name (Year) - Season 1.png") are ignored for the display.
"""

from PIL import Image
import os
from pathlib import Path
from math import ceil
import re
import argparse

# Configuration
gap_size = 10  # Pixels between images
target_aspect_ratio = 16 / 9  # Target aspect ratio for the overall display
poster_aspect_ratio = 2 / 3  # Standard poster aspect ratio (width/height)
max_image_width = 600  # Downsize individual images to this width (will be adjusted)
jpeg_quality = 85  # Quality for final output (1-100)


def extract_show_name_with_year(filename):
    """
    Extract the show name including year from a filename.
    Example: "Wacky Races (1968) - Season 1.png" -> "Wacky Races (1968)"
    """
    # Match pattern: anything up to and including (YEAR)
    match = re.match(r'^(.+?\(\d{4}\))', filename)
    if match:
        return match.group(1)
    
    # Fallback: if no year found, return the whole filename without extension
    return filename


def remove_leading_article(name):
    """
    Remove leading articles (The, A, An) from a name for sorting purposes.
    """
    # Convert to lowercase for comparison
    lower_name = name.lower()
    
    # Check and remove leading articles
    for article in ['the ', 'a ', 'an ']:
        if lower_name.startswith(article):
            return name[len(article):]
    
    return name


def is_parent_poster(filename):
    """
    Check if this is a parent poster (no season or specials info).
    Returns True if it's a main show poster.
    """
    # Exclude if it contains "Season " or "Specials"
    if "Season " in filename or "Specials" in filename or "Special" in filename:
        return False
    return True


def is_collection_poster(filename):
    """
    Check if this is a collection poster.
    Returns True if filename ends with "Collection" or "Productions"
    """
    return filename.endswith("Collection") or filename.endswith("Productions")


def sort_key_for_show(filepath):
    """
    Generate a sort key for show posters (alphabetically, ignoring articles).
    Uses natural sorting to handle numbers properly (e.g., 2 before 12).
    """
    filename = filepath.stem
    show_name = extract_show_name_with_year(filename)
    # Remove leading articles for alphabetical sorting
    show_name_for_sort = remove_leading_article(show_name).lower()
    
    # Split into text and number parts for natural sorting
    def natural_sort_key(text):
        """Convert text into a list of mixed strings and integers for natural sorting."""
        parts = []
        for part in re.split(r'(\d+)', text):
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(part)
        return parts
    
    return (natural_sort_key(show_name_for_sort), filename)


def calculate_optimal_rows(num_posters, target_ratio=target_aspect_ratio):
    """
    Calculate the optimal number of rows to achieve the target aspect ratio.
    
    Args:
        num_posters: Number of parent posters to display
        target_ratio: Target aspect ratio (width/height), default 16:9
    
    Returns:
        Optimal number of rows
    """
    if num_posters == 0:
        return 5  # Default fallback
    
    best_rows = 5
    best_diff = float('inf')
    
    # First, try to find layouts where all rows are perfectly filled
    perfect_layouts = []
    
    # Try different row counts from 2 to num_posters
    for rows in range(2, min(num_posters + 1, 20)):
        cols = ceil(num_posters / rows)
        
        # Calculate approximate dimensions (using normalized units)
        # Assume each poster has width=1, height=1.5 (standard poster ratio)
        poster_width = 1
        poster_height = poster_width / poster_aspect_ratio
        
        # Collection dimensions (matches rows in height)
        collection_height = rows * poster_height + (rows - 1) * (gap_size / max_image_width)
        collection_width = collection_height * poster_aspect_ratio
        
        # Right section dimensions
        right_width = cols * poster_width + (cols - 1) * (gap_size / max_image_width)
        
        # Total dimensions (with gaps)
        total_width = collection_width + (3 * gap_size / max_image_width) + right_width
        total_height = collection_height + (2 * gap_size / max_image_width)
        
        # Calculate aspect ratio
        aspect_ratio = total_width / total_height
        diff = abs(aspect_ratio - target_ratio)
        
        # Check if all rows are full
        if num_posters % rows == 0:
            perfect_layouts.append((rows, diff))
        elif diff < best_diff:
            # Track best imperfect layout as fallback
            best_diff = diff
            best_rows = rows
    
    # If we found any perfect layouts, choose the one closest to target ratio
    if perfect_layouts:
        best_rows = min(perfect_layouts, key=lambda x: x[1])[0]
    
    return best_rows


def get_image_files(input_dir="input"):
    """Get collection and parent poster image files from the input directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' not found")
    
    # Get all image files
    all_image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    # Separate collection and parent posters
    collection_poster = None
    parent_posters = []
    
    for f in all_image_files:
        if is_collection_poster(f.stem):
            if collection_poster is None:
                collection_poster = f
            # If there are multiple collections, just use the first one
        elif is_parent_poster(f.stem):
            parent_posters.append(f)
    
    # Sort parent posters alphabetically
    parent_posters = sorted(parent_posters, key=sort_key_for_show)
    
    return collection_poster, parent_posters


def resize_image_for_grid(img, target_width):
    """Resize an image to target width while maintaining aspect ratio."""
    aspect_ratio = img.height / img.width
    target_height = int(target_width * aspect_ratio)
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def create_pretty_display(collection_file, parent_files, target_width=max_image_width, rows=None):
    """
    Create a display with collection poster on left and parent posters in specified rows on right.
    If rows is None, it will be calculated automatically.
    """
    # Calculate optimal rows if not specified
    if rows is None:
        rows = calculate_optimal_rows(len(parent_files))
    
    print(f"Using {rows} rows for layout")
    # Load and resize parent posters first to get their dimensions
    parent_images = []
    for img_file in parent_files:
        img = Image.open(img_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_resized = resize_image_for_grid(img, target_width)
        parent_images.append(img_resized)
    
    if not parent_images:
        # If no parent posters, just resize collection normally
        collection_img = Image.open(collection_file)
        if collection_img.mode != 'RGB':
            collection_img = collection_img.convert('RGB')
        collection_resized = resize_image_for_grid(collection_img, target_width * 2)
        grid_width = collection_resized.width + (2 * gap_size)
        grid_height = collection_resized.height + (2 * gap_size)
        grid_image = Image.new('RGB', (grid_width, grid_height), color='black')
        grid_image.paste(collection_resized, (gap_size, gap_size))
        return grid_image
    
    # Calculate dimensions based on parent posters
    cell_width = parent_images[0].width
    cell_height = parent_images[0].height
    
    # Load and resize collection poster to match exactly the specified number of rows
    collection_img = Image.open(collection_file)
    if collection_img.mode != 'RGB':
        collection_img = collection_img.convert('RGB')
    # Calculate collection height to match rows of parent posters plus gaps between them
    target_collection_height = (rows * cell_height) + ((rows - 1) * gap_size)
    target_collection_width = int(target_collection_height / (collection_img.height / collection_img.width))
    collection_resized = collection_img.resize((target_collection_width, target_collection_height), Image.Resampling.LANCZOS)
    
    # Recalculate dimensions with properly sized collection
    cell_width = parent_images[0].width
    cell_height = parent_images[0].height
    
    # Arrange parent posters in specified number of rows
    num_parents = len(parent_images)
    cols_needed = ceil(num_parents / rows)
    
    # Calculate total dimensions
    # Left side: collection poster (matches the specified number of rows)
    collection_width = collection_resized.width
    collection_height = collection_resized.height
    
    # Right side: parent posters in specified rows
    right_section_width = (cols_needed * cell_width) + ((cols_needed - 1) * gap_size)
    right_section_height = (rows * cell_height) + ((rows - 1) * gap_size)
    
    # Total grid dimensions with borders
    grid_width = (3 * gap_size) + collection_width + right_section_width
    grid_height = (2 * gap_size) + right_section_height  # Use right section height (they match now)
    
    # Create canvas
    grid_image = Image.new('RGB', (grid_width, grid_height), color='black')
    
    # Paste collection poster on the left
    grid_image.paste(collection_resized, (gap_size, gap_size))
    
    # Paste parent posters on the right (in specified rows)
    x_offset = (2 * gap_size) + collection_width
    
    for idx, img in enumerate(parent_images):
        row = idx // cols_needed  # Fill left to right first
        col = idx % cols_needed
        x = x_offset + col * (cell_width + gap_size)
        y = gap_size + row * (cell_height + gap_size)
        grid_image.paste(img, (x, y))
    
    return grid_image


def main():
    """Main function to generate the pretty display."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate a pretty display with a collection poster and parent posters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Poster Naming Scheme:
  - Collection posters should end with "Collection" or "Productions"
  - Parent posters should be named as "<Show or Movie Name> (Year)"
  - Season/specials posters are ignored for the display
        '''
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='input',
        help='Input folder containing poster images (default: input)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output.jpg',
        help='Output filename (default: output.jpg)'
    )
    
    args = parser.parse_args()
    
    print("=== Pretty Collection Display Generator ===\n")
    
    # Get collection and parent poster files
    collection_file, parent_files = get_image_files(args.input)
    
    if collection_file is None:
        print("Error: No collection poster found in input/ directory")
        print("(Looking for files ending with 'Collection' or 'Productions')")
        return
    
    print(f"Collection poster: {collection_file.name}")
    print(f"Found {len(parent_files)} parent posters\n")
    
    if parent_files:
        print("Parent posters:")
        print("-" * 60)
        for idx, img_file in enumerate(parent_files, 1):
            show_name = extract_show_name_with_year(img_file.stem)
            print(f"{idx}. {img_file.name}")
        print("-" * 60)
    
    # Calculate layout
    if parent_files:
        num_rows = calculate_optimal_rows(len(parent_files))
        cols = ceil(len(parent_files) / num_rows)
        actual_aspect = 16 / 9
        print(f"\nLayout (targeting {target_aspect_ratio:.2f}:1 aspect ratio):")
        print(f"  Collection: {num_rows} rows tall (left)")
        print(f"  Parent posters: {num_rows} rows × {cols} columns (right)")
    else:
        num_rows = 5  # Default if no parent posters
    
    # Create the display
    print(f"\nGenerating display (resizing images to {max_image_width}px width)...")
    grid_image = create_pretty_display(collection_file, parent_files, max_image_width, rows=num_rows)
    
    # Save the result
    print(f"Saving to {args.output}...")
    grid_image.save(args.output, 'JPEG', quality=jpeg_quality, optimize=True)
    
    # Get file size
    file_size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\n✓ Display created successfully!")
    print(f"  Output: {args.output}")
    print(f"  Dimensions: {grid_image.width}x{grid_image.height}px")
    print(f"  File size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    main()
