# Import/Export Harry Potter and the Deathly Hallows
A Blender add-on for importing assets extracted from Harry Potter and the Deathly Hallows - Part 1 and Harry Potter and the Deathly Hallows - Part 2. Blender 4.2 or newer is required.

## Installation
1. Download the latest entry from the [releases](https://github.com/jmancoder/io-deathly-hallows/releases) page.
2. In Blender, open Edit->Preferences->Add-ons.
3. Expand the dropdown on the top right and click "Install from Disk...".
4. Select the downloaded .zip file.

## Usage
1. Extract a .bin.gz archive using [this](https://github.com/jmancoder/deathly-hallows-extractor) script.
2. Open Blender, press N to expand the sidebar, and open the "Deathly Hallows" tab.
3. Set the "Game" property appropriately.
4. Click the folder icon beside "Manifest Path" and select the extracted manifest.json file.
5. If importing from Deathly Hallows 2, extract delta-global.bin.gz with the aforementioned script and point "Delta Manifest Path" to its manifest.json file.
6. To import a level or prop mesh, click "Import MSH". To import a character mesh, click "Import SKL". To import an individual texture, click "Import TEX".
7. Optionally, select all objects with A and rotate them with R->90.

## TODO:
- Handle all vertex types in Deathly Hallows 2 shape files
- Properly apply detail and mask textures
- Create node groups for more shader types
- Export shape files
