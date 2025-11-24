# Urban Green Routing

Urban Green Routing is a small open-source project to compute tree-optimized walking routes in cities. It uses NAIP imagery, SAM segmentation, and OpenStreetMap street networks to create vectorized tree data, calculate a green index per street, and identify the greenest walkable paths.

## Project Pipeline

1. Download NAIP imagery for a city
2. Segment trees using SAM
3. Convert raster trees into vector GIS features
4. Create a street graph and calculate green index per street
5. Plan the greenest walking routes

## Stack

- Python 3.x
- SAM (Segment Anything Model)
- rasterio, geopandas, shapely
- networkx
- OSMnx

## Status

Early-stage: project skeleton and pipeline planned.
