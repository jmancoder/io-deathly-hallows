# Import/Export Harry Potter and the Deathly Hallows
A Blender extension for importing meshes from Harry Potter and the Deathly Hallows - Part 1. Blender 4.2 and newer is supported.

## Usage
1. Extract a .bin.gz archive using [this](https://github.com/jmancoder/deathly-hallows-extractor) script.
2. Open Blender, press N to expand the sidebar, and open the "Deathly Hallows" tab.
3. Set the "Game" property appropriately.
4. Click the folder icon beside "Manifest Path" and select the extracted manifest.json file.
5. If importing from Deathly Hallows 2, extract delta-global.bin.gz with the aforementioned script and point "Delta Manifest Path" to its manifest.json file.
6. To import a level or prop mesh, click "Import MSH". To import a character mesh, click "Import SKL". To import an individual texture, click "Import TEX".
7. Optionally, select all objects with A and rotate them with R->90.

## TODO:
- Handle all vertex types in Deathly Hallows 2 shapes
- Properly apply detail and mask textures
- Export shape files
