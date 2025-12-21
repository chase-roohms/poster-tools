# Copilot Instructions for poster-tools

## Project Overview
This repository contains tools for creating pretty poster displays and automating Photoshop workflows for poster collections.

## Important File Type Note
**All `.jsx` files in this repository are ExtendScript (Adobe Photoshop scripting language), NOT JavaScript.**
- ExtendScript is based on ECMAScript 3 specification
- No modern JavaScript features (no arrow functions, const/let, template literals, etc.)
- Uses Photoshop DOM API (e.g., `app.activeDocument`, `doc.layers`, etc.)
- Target directive: `#target photoshop`
- File operations use `Folder` and `File` objects, not Node.js APIs

### Python Scripts
Pillow (PIL) is used for image processing tasks.

### Photoshop Scripts (`ps-scripts/`)
All scripts in this directory are ExtendScript for Adobe Photoshop

## Naming Conventions
- **Collection posters**: Filenames ending with "Collection" or "Productions" (e.g., "Pixar Collection.png")
- **Parent posters**: Named as "<Show or Movie Name> (Year)" (e.g., "Wacky Races (1968).png")
- **Season/special posters**: Format includes season info (e.g., "Show Name (Year) - Season 1.png")

## Dependencies
- **Python**: Pillow >= 10.0.0
- **Photoshop**: Required for running ExtendScript (.jsx) files

## Coding Guidelines
- **ExtendScript**: Use ECMAScript 3 syntax only, with Photoshop DOM API
- **Python**: Follow standard Python conventions, use type hints where appropriate
- **Image processing**: Default poster aspect ratio is 2:3 (width/height)
- **Display generation**: Target 16:9 aspect ratio with configurable tolerance
