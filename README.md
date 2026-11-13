# Import/Export Harry Potter and the Deathly Hallows
A Blender extension for importing meshes from Harry Potter and the Deathly Hallows - Part 1. Blender 4.2 and newer is supported.

## Usage
1. Extract a .bin.gz archive using [this](https://github.com/jmancoder/deathly-hallows-extractor) script.
2. Open Blender and press N to expand the sidebar.
3. Open the "Deathly Hallows" tab and expand "Deathly Hallows IO".
4. Click the folder icon beside "Manifest Path" and select manifest.json from the extracted files.
5. Open manifest.json in a text editor and search for "MSH:" to see which files you can import.
6. In Blender, click "Import MSH" and select the desired file. Dependant shape, material, and texture files will import automatically.
7. Optionally select all objects and rotate them 90 degrees on the x-axis.

## TODO:
- Properly apply detail and mask textures
- Export shape files
- Import character meshes
- Add support for Harry Potter and the Deathly Hallows - Part 2
