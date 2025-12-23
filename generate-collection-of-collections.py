#!/usr/bin/env python3
"""
Generate a collection-of-collections display with a main collection poster (full height) on the left
and movie collections organized in columns with standalones in their own column.

Poster Naming Scheme:
- Main collection poster should have filename ending with "Collection" or "Productions" (e.g., "MCU Collection.png").
- Movie posters should be numbered sequentially (e.g., "Captain America 0.png", "Captain America 1.png").
- Standalone movies (without numbered collections) go in their own column.
"""

from PIL import Image, ImageFilter
import os
from pathlib import Path
from math import ceil
import re
import argparse
from collections import defaultdict

# Configuration
gap_size = 20  # Pixels between images
poster_aspect_ratio = 2 / 3  # Standard poster aspect ratio (width/height)
max_image_width = 600  # Downsize individual images to this width
jpeg_quality = 85  # Quality for final output (1-100)


def is_collection_poster(filename):
    """
    Check if this is a main collection poster.
    Returns True if filename ends with "Collection" or "Productions"
    """
    return filename.endswith("Collection") or filename.endswith("Productions")


def parse_movie_name(filename):
    """
    Parse a movie filename to extract collection name and number.
    
    Examples:
        "Captain America 0.png" -> ("Captain America", 0)
        "Iron Man 1.png" -> ("Iron Man", 1)
        "Thunderbolts.png" -> ("Thunderbolts", None)
    
    Returns:
        (collection_name, number) or (movie_name, None) for standalone movies
    """
    # Try to match pattern: "Name Number" where number is at the end
    match = re.match(r'^(.+?)\s+(\d+)$', filename)
    if match:
        collection_name = match.group(1).strip()
        number = int(match.group(2))
        return (collection_name, number)
    
    # No number found, it's a standalone movie
    return (filename, None)


def group_movies_by_collection(movie_files):
    """
    Group movie files by their collection name.
    
    Returns:
        collections: dict of {collection_name: [(number, filepath), ...]}
        standalones: list of filepaths for standalone movies
    """
    collections = defaultdict(list)
    standalones = []
    
    for filepath in movie_files:
        filename = filepath.stem
        collection_name, number = parse_movie_name(filename)
        
        if number is None:
            # Standalone movie
            standalones.append(filepath)
        else:
            # Part of a collection
            collections[collection_name].append((number, filepath))
    
    # Sort each collection by number
    for collection_name in collections:
        collections[collection_name].sort(key=lambda x: x[0])
    
    # Sort collections by size (number of movies) descending, then alphabetically
    sorted_collections = dict(sorted(collections.items(), key=lambda x: (-len(x[1]), x[0])))
    
    # Sort standalones alphabetically
    standalones.sort(key=lambda x: x.stem)
    
    return sorted_collections, standalones


def get_image_files(input_dir="input"):
    """Get collection poster, movie poster, and optional background files from the input directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' not found")
    
    # Get all image files
    all_image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    # Separate main collection poster, background, and movie posters
    collection_poster = None
    background_image = None
    movie_posters = []
    
    for f in all_image_files:
        if is_collection_poster(f.stem):
            if collection_poster is None:
                collection_poster = f
            # If there are multiple collections, just use the first one
        elif f.stem == "Background":
            background_image = f
        else:
            movie_posters.append(f)
    
    return collection_poster, movie_posters, background_image


def resize_image_for_grid(img, target_width):
    """Resize an image to target width while maintaining aspect ratio."""
    aspect_ratio = img.height / img.width
    target_height = int(target_width * aspect_ratio)
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def create_collection_display(collection_file, collections, standalones, background_file=None, target_width=max_image_width):
    """
    Create a display with main collection poster on left and movie collections organized in columns on right.
    Collections fill down two columns, standalones get their own column on the far right.
    """
    # Calculate total number of rows needed
    # Height is determined by collections only, standalones wrap horizontally if needed
    has_standalones = len(standalones) > 0
    total_collections = len(collections)
    total_rows = ceil(total_collections / 2)
    
    if total_rows == 0:
        # If no movies at all, just show the collection poster
        collection_img = Image.open(collection_file)
        if collection_img.mode != 'RGB':
            collection_img = collection_img.convert('RGB')
        collection_resized = resize_image_for_grid(collection_img, target_width * 2)
        grid_width = collection_resized.width + (2 * gap_size)
        grid_height = collection_resized.height + (2 * gap_size)
        grid_image = Image.new('RGB', (grid_width, grid_height), color='black')
        grid_image.paste(collection_resized, (gap_size, gap_size))
        return grid_image, []
    
    # Load all movie images
    all_movie_images = []
    row_data = []  # List of (row_index, column_index, collection_name, images_for_collection)
    
    # Load collection rows (two collection columns)
    collection_items = list(collections.items())
    
    for idx, (collection_name, movies) in enumerate(collection_items):
        col_idx = idx // total_rows  # Fill left column first, then right
        row_idx = idx % total_rows   # Which row within that column
        
        collection_images = []
        for number, filepath in movies:
            img = Image.open(filepath)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_resized = resize_image_for_grid(img, target_width)
            collection_images.append(img_resized)
            all_movie_images.append(img_resized)
        row_data.append((row_idx, col_idx, collection_name, collection_images))
    
    # Load standalones - arrange in grid, filling down first column then wrapping to next column
    standalone_data = []
    if has_standalones:
        for idx, filepath in enumerate(standalones):
            img = Image.open(filepath)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_resized = resize_image_for_grid(img, target_width)
            all_movie_images.append(img_resized)
            
            # Calculate row and column within standalone section
            standalone_row = idx % total_rows
            standalone_col = idx // total_rows
            standalone_data.append((standalone_row, standalone_col, filepath.stem, img_resized))
    
    # Get dimensions from first movie poster
    cell_width = all_movie_images[0].width
    cell_height = all_movie_images[0].height
    
    # Calculate maximum number of movies in each column separately
    left_column_collections = [collection_images for _, col_idx, _, collection_images in row_data if col_idx == 0]
    right_column_collections = [collection_images for _, col_idx, _, collection_images in row_data if col_idx == 1]
    
    max_movies_left = max(len(c) for c in left_column_collections) if left_column_collections else 0
    max_movies_right = max(len(c) for c in right_column_collections) if right_column_collections else 0
    
    # Standalones column - calculate how many columns needed
    standalone_cols_needed = ceil(len(standalones) / total_rows) if has_standalones else 0
    
    # Calculate width for each column
    left_column_width = max_movies_left * cell_width + (max_movies_left - 1) * gap_size
    right_column_width = max_movies_right * cell_width + (max_movies_right - 1) * gap_size
    standalone_column_width = (standalone_cols_needed * cell_width + (standalone_cols_needed - 1) * gap_size) if has_standalones else 0
    
    # Load and resize main collection poster to match total rows
    collection_img = Image.open(collection_file)
    if collection_img.mode != 'RGB':
        collection_img = collection_img.convert('RGB')
    
    # Calculate collection height to match all rows
    target_collection_height = (total_rows * cell_height) + ((total_rows - 1) * gap_size)
    target_collection_width = int(target_collection_height / (collection_img.height / collection_img.width))
    collection_resized = collection_img.resize((target_collection_width, target_collection_height), Image.Resampling.LANCZOS)
    
    # Calculate total dimensions
    collection_width = collection_resized.width
    collection_height = collection_resized.height
    
    right_section_width = left_column_width + (gap_size * 10) + right_column_width
    if has_standalones:
        right_section_width += (gap_size * 10) + standalone_column_width
    right_section_height = (total_rows * cell_height) + ((total_rows - 1) * gap_size)
    
    # Total grid dimensions with borders
    grid_width = gap_size + collection_width + (gap_size * 10) + right_section_width + gap_size
    grid_height = (2 * gap_size) + right_section_height
    
    # Create canvas
    grid_image = Image.new('RGB', (grid_width, grid_height), color='black')
    
    # If background image provided, blur it and use as background
    if background_file:
        bg_img = Image.open(background_file)
        if bg_img.mode != 'RGB':
            bg_img = bg_img.convert('RGB')
        # Resize background to fit canvas
        bg_img = bg_img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
        # Apply heavy blur
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=50))
        grid_image.paste(bg_img, (0, 0))
    
    # Paste collection poster on the left
    grid_image.paste(collection_resized, (gap_size, gap_size))
    
    # Paste movie collections on the right (two collection columns)
    x_offset = gap_size + collection_width + (gap_size * 10)
    
    for row_idx, col_idx, collection_name, collection_images in row_data:
        # Calculate starting x position for this collection
        if col_idx == 0:
            collection_x_start = x_offset
        else:
            collection_x_start = x_offset + left_column_width + (gap_size * 10)
        
        # Paste each movie in the collection
        for movie_idx, img in enumerate(collection_images):
            x = collection_x_start + movie_idx * (cell_width + gap_size)
            y = gap_size + row_idx * (cell_height + gap_size)
            grid_image.paste(img, (x, y))
    
    # Paste standalones in their own column area (wraps horizontally if needed)
    if has_standalones:
        standalone_x_start = x_offset + left_column_width + (gap_size * 10) + right_column_width + (gap_size * 10)
        for standalone_row, standalone_col, movie_name, img in standalone_data:
            x = standalone_x_start + standalone_col * (cell_width + gap_size)
            y = gap_size + standalone_row * (cell_height + gap_size)
            grid_image.paste(img, (x, y))
    
    return grid_image, row_data


def main():
    """Main function to generate the collection-of-collections display."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate a collection-of-collections display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Poster Naming Scheme:
  - Main collection poster should end with "Collection" or "Productions"
  - Movie posters should be numbered sequentially (e.g., "Captain America 0.png")
  - Standalone movies go in their own column
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
        default='collection-of-collections.jpg',
        help='Output filename (default: collection-of-collections.jpg)'
    )
    
    args = parser.parse_args()
    
    print("=== Collection-of-Collections Display Generator ===\n")
    
    # Get collection poster and movie files
    collection_file, movie_files, background_file = get_image_files(args.input)
    
    if collection_file is None:
        print("Error: No main collection poster found in input/ directory")
        print("(Looking for files ending with 'Collection' or 'Productions')")
        return
    
    print(f"Main collection poster: {collection_file.name}")
    if background_file:
        print(f"Background image: {background_file.name}")
    print(f"Found {len(movie_files)} movie posters\n")
    
    # Group movies by collection
    collections, standalones = group_movies_by_collection(movie_files)
    
    # Display summary
    print("Movie Collections:")
    print("-" * 60)
    for collection_name, movies in collections.items():
        movie_names = [f"{collection_name} {num}" for num, _ in movies]
        print(f"  {collection_name}: {len(movies)} movies")
        print(f"    {', '.join(movie_names)}")
    
    if standalones:
        print(f"\n  Standalone movies: {len(standalones)}")
        for filepath in standalones:
            print(f"    {filepath.stem}")
    
    print("-" * 60)
    
    # Calculate layout
    total_collections_for_display = len(collections)
    total_rows = ceil(total_collections_for_display / 2)
    standalone_cols_needed = ceil(len(standalones) / total_rows) if standalones else 0
    print(f"\nLayout:")
    print(f"  Main collection: {total_rows} rows tall (left)")
    print(f"  Movie collections: {len(collections)} collections in 2 columns (left/middle)")
    if standalones:
        print(f"  Standalone movies: {len(standalones)} movies in {standalone_cols_needed} column(s) (right)")
    
    # Create the display
    print(f"\nGenerating display (resizing images to {max_image_width}px width)...")
    grid_image, row_data = create_collection_display(
        collection_file, collections, standalones, background_file, max_image_width
    )
    
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
