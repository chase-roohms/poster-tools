#!/usr/bin/env python3
"""
Generate a collection-of-collections display with a main collection poster (full height) on the left
and movie collections organized in columns with standalones in their own column.

Poster Naming Scheme:
- Main collection poster should have filename ending with "Collection" or "Productions" (e.g., "MCU Collection.png").
- Movie posters should be numbered sequentially (e.g., "Captain America 0.png", "Captain America 1.png").
- Standalone movies (without numbered collections) go in their own column.
"""

from PIL import Image, ImageFilter, ImageDraw, ImageFont
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
collection_columns = 3  # Number of columns for movie collections
reddit_username = "ChaseDak"  # For credit in output if desired
tpdb_username = "NeonVariant"  # For credit in output if desired

# Footer configuration
footer_height = 80  # Height of footer section in pixels
footer_icon_size = 40  # Size of social media icons
footer_padding = 20  # Padding around footer content
footer_spacing = 60  # Spacing between Reddit and TPDB sections


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


def add_footer(image, reddit_user, tpdb_user):
    """Add a footer with Reddit and ThePosterDatabase credits."""
    # Check if icon files exist
    assets_path = Path('assets')
    reddit_icon_path = assets_path / 'reddit-icon.png'
    tpdb_icon_path = assets_path / 'tpdb-icon.png'
    
    if not reddit_icon_path.exists() or not tpdb_icon_path.exists():
        print("Warning: Footer icons not found in assets/ directory. Skipping footer.")
        return image
    
    # Dynamically scale footer based on image width
    # Footer height is 2.5% of image width, minimum 80px
    dynamic_footer_height = max(footer_height, int(image.width * 0.025))
    # Icon size is 1.8% of image width, minimum 40px
    dynamic_icon_size = max(footer_icon_size, int(image.width * 0.018))
    # Font size scales with image width
    dynamic_font_size = max(24, int(image.width * 0.010))
    # Spacing scales too
    dynamic_spacing = max(footer_spacing, int(image.width * 0.025))
    dynamic_icon_text_gap = max(footer_padding, int(image.width * 0.005))
    
    # Create new image with footer space
    new_width = image.width
    new_height = image.height + dynamic_footer_height
    
    # Create base RGB image and paste original
    footer_image = Image.new('RGB', (new_width, new_height), color='black')
    footer_image.paste(image, (0, 0))
    
    # Extend the bottom edge of the image into footer area to show transparency effect
    # Take the bottom 1px row and stretch it to fill footer area
    footer_y_start = image.height
    bottom_edge = image.crop((0, image.height - 1, image.width, image.height))
    bottom_extended = bottom_edge.resize((new_width, dynamic_footer_height), Image.Resampling.NEAREST)
    footer_image.paste(bottom_extended, (0, footer_y_start))
    
    # Create semi-transparent footer overlay
    footer_overlay = Image.new('RGBA', (new_width, new_height), color=(0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(footer_overlay)
    
    # Draw semi-transparent black rectangle for footer area
    draw_overlay.rectangle(
        [(0, footer_y_start), (new_width, new_height)],
        fill=(0, 0, 0, 128)
    )
    
    # Composite the overlay onto the base image
    footer_image = Image.alpha_composite(footer_image.convert('RGBA'), footer_overlay).convert('RGB')
    
    # Load and resize icons
    reddit_icon = Image.open(reddit_icon_path).convert('RGBA')
    tpdb_icon = Image.open(tpdb_icon_path).convert('RGBA')
    
    reddit_icon = reddit_icon.resize((dynamic_icon_size, dynamic_icon_size), Image.Resampling.LANCZOS)
    tpdb_icon = tpdb_icon.resize((dynamic_icon_size, dynamic_icon_size), Image.Resampling.LANCZOS)
    
    # Calculate positions for centered footer content
    footer_y_start = image.height
    icon_y = footer_y_start + (dynamic_footer_height - dynamic_icon_size) // 2
    
    # Create drawing context
    draw = ImageDraw.Draw(footer_image)
    
    # Try to load a modern font with dynamic size, fall back if not available
    font_paths = [
        '/System/Library/Fonts/Supplemental/Roboto-Regular.ttf',  # Roboto
        '/Library/Fonts/Roboto-Regular.ttf',  # Roboto (user-installed)
        '~/Library/Fonts/Roboto-Regular.ttf',  # Roboto (user fonts)
        '/System/Library/Fonts/Avenir.ttc',  # Avenir - modern geometric
        '/System/Library/Fonts/Supplemental/Futura.ttc',  # Futura - geometric
        '/System/Library/Fonts/Supplemental/Gotham.ttf',  # Gotham if available
        '/System/Library/Fonts/Helvetica.ttc',  # Fallback
    ]
    
    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, dynamic_font_size)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # Measure text sizes
    reddit_text = f"u/{reddit_user}"
    tpdb_text = f"@{tpdb_user}"
    
    # Calculate bounding boxes for text
    reddit_bbox = draw.textbbox((0, 0), reddit_text, font=font)
    tpdb_bbox = draw.textbbox((0, 0), tpdb_text, font=font)
    reddit_text_width = reddit_bbox[2] - reddit_bbox[0]
    tpdb_text_width = tpdb_bbox[2] - tpdb_bbox[0]
    text_height = reddit_bbox[3] - reddit_bbox[1]
    
    # Calculate total width for both sections
    reddit_section_width = dynamic_icon_size + dynamic_icon_text_gap + reddit_text_width
    tpdb_section_width = dynamic_icon_size + dynamic_icon_text_gap + tpdb_text_width
    total_content_width = reddit_section_width + dynamic_spacing + tpdb_section_width
    
    # Center everything
    start_x = (new_width - total_content_width) // 2
    
    # Reddit section
    reddit_icon_x = start_x
    reddit_text_x = reddit_icon_x + dynamic_icon_size + dynamic_icon_text_gap
    # Better vertical centering: align text baseline with icon center, accounting for descenders
    text_y = footer_y_start + (dynamic_footer_height - text_height) // 2 - reddit_bbox[1]
    
    # Paste Reddit icon with transparency
    footer_image.paste(reddit_icon, (reddit_icon_x, icon_y), reddit_icon)
    draw.text((reddit_text_x, text_y), reddit_text, fill='white', font=font)
    
    # TPDB section
    tpdb_icon_x = reddit_text_x + reddit_text_width + dynamic_spacing
    tpdb_text_x = tpdb_icon_x + dynamic_icon_size + dynamic_icon_text_gap
    
    # Paste TPDB icon with transparency
    footer_image.paste(tpdb_icon, (tpdb_icon_x, icon_y), tpdb_icon)
    draw.text((tpdb_text_x, text_y), tpdb_text, fill='white', font=font)
    
    return footer_image


def create_collection_display(collection_file, collections, standalones, background_file=None, target_width=max_image_width, num_columns=2):
    """
    Create a display with main collection poster on left and movie collections organized in columns on right.
    Collections fill down multiple columns, standalones get their own column on the far right.
    """
    # Calculate total number of rows needed
    # Height is determined by collections only, standalones wrap horizontally if needed
    has_standalones = len(standalones) > 0
    total_collections = len(collections)
    total_rows = ceil(total_collections / num_columns)
    
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
    column_widths = []
    for col in range(num_columns):
        col_collections = [collection_images for _, col_idx, _, collection_images in row_data if col_idx == col]
        max_movies = max(len(c) for c in col_collections) if col_collections else 0
        col_width = max_movies * cell_width + (max_movies - 1) * gap_size if max_movies > 0 else 0
        column_widths.append(col_width)
    
    # Standalones column - calculate how many columns needed
    standalone_cols_needed = ceil(len(standalones) / total_rows) if has_standalones else 0
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
    
    # Sum up all collection column widths with gaps
    right_section_width = sum(column_widths)
    if len(column_widths) > 1:
        right_section_width += (gap_size * 10) * (len(column_widths) - 1)
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
    
    # Paste movie collections on the right (multiple collection columns)
    x_offset = gap_size + collection_width + (gap_size * 10)
    
    for row_idx, col_idx, collection_name, collection_images in row_data:
        # Calculate starting x position for this collection
        collection_x_start = x_offset
        for i in range(col_idx):
            collection_x_start += column_widths[i] + (gap_size * 10)
        
        # Paste each movie in the collection
        for movie_idx, img in enumerate(collection_images):
            x = collection_x_start + movie_idx * (cell_width + gap_size)
            y = gap_size + row_idx * (cell_height + gap_size)
            grid_image.paste(img, (x, y))
    
    # Paste standalones in their own column area (wraps horizontally if needed)
    if has_standalones:
        standalone_x_start = x_offset
        for col_width in column_widths:
            standalone_x_start += col_width + (gap_size * 10)
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
    parser.add_argument(
        '-c', '--columns',
        type=int,
        default=collection_columns,
        help=f'Number of columns for movie collections (default: {collection_columns})'
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
    total_rows = ceil(total_collections_for_display / args.columns)
    standalone_cols_needed = ceil(len(standalones) / total_rows) if standalones else 0
    print(f"\nLayout:")
    print(f"  Main collection: {total_rows} rows tall (left)")
    print(f"  Movie collections: {len(collections)} collections in {args.columns} column(s) (middle)")
    if standalones:
        print(f"  Standalone movies: {len(standalones)} movies in {standalone_cols_needed} column(s) (right)")
    
    # Create the display
    print(f"\nGenerating display (resizing images to {max_image_width}px width)...")
    grid_image, row_data = create_collection_display(
        collection_file, collections, standalones, background_file, max_image_width, args.columns
    )
    
    # Add footer with credits
    print("Adding footer with credits...")
    final_image = add_footer(grid_image, reddit_username, tpdb_username)
    
    # Save the result
    print(f"Saving to {args.output}...")
    final_image.save(args.output, 'JPEG', quality=jpeg_quality, optimize=True)
    
    # Get file size
    file_size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\n✓ Display created successfully!")
    print(f"  Output: {args.output}")
    print(f"  Dimensions: {final_image.width}x{final_image.height}px")
    print(f"  File size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    main()
