# Urban Green Routing

Urban Green Routing is a small open-source project to compute tree-optimized walking routes in cities. It uses NAIP imagery, Detectree segmentation, and OpenStreetMap street networks to create vectorized tree data, calculate a green index per street, and identify the greenest walkable paths.

## Project Pipeline

1. Download NAIP imagery for a city  
2. Segment trees using Detectree  
3. Convert raster trees into vector GIS features  
4. Create a street graph and calculate green index per street  
5. Plan the greenest walking routes

## Stack

- Python 3.x  
- Detectree (replacing SAM for tree segmentation)  
- rasterio, geopandas, shapely  
- networkx  
- OSMnx

## Status

**NAIP Downloader:** Fully modular, parameterized, and testable; can run standalone via main.

**OSM Downloader:** Fully modular, parameterized, and testable; can run standalone via main.

**Tree Detector (Detectree):** Functional but in an initial stage; improvements and optimizations ongoing.

**Data Handling & Utilities:** User inputs, AOI conversion, bounding boxes, and tile calculations are implemented; folder management centralized.

**Code Structure:** Clear separation of responsibilities across modules; scripts are concise (~50 lines each) and maintainable.
