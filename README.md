## Urban Green Routing

**Urban Green Routing** is a tree-optimized walking routing tool that computes routes favoring streets with higher tree coverage, based on NAIP satellite imagery, tree canopy segmentation, and OpenStreetMap street networks.

---
## Background & Motivation

Urban walkability is strongly influenced by greenery. Trees improve the pedestrian experience, reduce heat, and increase overall well-being. Urban Green Routing is designed as a GIS engineering project to quantify greenery along streets and compute routes that maximize tree coverage while remaining practical for walking.

---
## **User Input**

The user provides configuration for three main components:

**Area of Interest (AOI)**

- Name and bounding box (southwest and northeast coordinates) defining the area where routing is performed

**Imagery Resolution**

- Defines the spatial resolution for NAIP satellite imagery. Higher resolution improves tree detection detail, which affects route optimization

**Routing Options**

- Shortest: prioritize minimal distance
- Greenest: favor streets with higher tree coverage

---

## **Processing Pipeline**

1. **Data Acquisition**

- Download NAIP satellite imagery for the AOI
- Extract street network from OpenStreetMap for the same AOI using OSMnx
  
2. **Tree Detection**  

- Segment trees from NAIP satellite imagery using Detectree
- Raster processing, reprojection, and vectorization using NumPy, Rasterio, and Shapely

3. **Vector & Geometry Processing**

- Reproject vector layers using GeoPandas
- Buffer street segments and trees to calculate overlap ("influence zone")
- Compute the percentage of street segment buffer area covered by trees
- Geometry operations (buffering, clipping) using GeoPandas

4. **Routing**

- Build a street graph using NetworkX
- Plan routes according to the user's selected routing option
- Save final route as a GeoPackage including geometry, total length, and green influence weight

---

## **Architecture / Project Structure**

```text
data/
├── raw/          # files from each processing step
├── processed/    # output routes

docs/
└── green_routing_example.png  # screenshot placeholder

src/
├── utils/
│   ├── geometry.py
│   ├── inputs.py
│   └── paths.py
├── download_naip.py
├── download_osm.py
├── detect_trees.py
├── process_vectors.py
├── reproject_layers.py
├── green_routing.py
└── main.py
```

---

## **Technology Stack**

- **Python 3.x**  
- **Data Acquisition**  
  - requests: download NAIP satellite imagery
  - pyproj: bbox coordinate transformations
  - OSMnx: street network extraction from OpenStreetMap

- **Tree Detection & Raster Processing**  
  - Detectree: tree canopy segmentation
  - rasterio: raster I/O, reprojection, vectorization
  - NumPy: raster array manipulation
  - Shapely: raster to vector conversion

- **Geospatial Vector Processing**  
  - GeoPandas: vector data handling

- **Routing**
  - NetworkX: graph construction and routing

---

## **Output**

The final route is saved as a **GeoPackage file** containing:

- Route geometry (`LineString`)  
- Aggregated metrics: total route length and total green influence weight  

**Visualization:**  

![Tree-optimized routing example](docs/green_routing_example.png)  
*Screenshot placeholder – to be replaced with actual routing example*  

The map should illustrate:

- Street segments colored by **green influence weight**  
- Tree masks overlaid  
- Example routes:  
  - **Shortest path** (distance only)  
  - **Greenest path** (based on green influence)  

> Greenest routing combines street segment length with tree coverage influence to compute a balanced path.

---

## **Project Status**

- **NAIP Downloader:** fully implemented
- **OSM Downloader:** fully implemented
- **Tree Detector (Detectree):** fully implemented
- **Routing Module:** fully implemented
- **Data Handling & Utilities:** fully implemented
- **Processing Pipeline:** fully implemented
- **Code Structure:** clear separation of responsibilities; scripts are concise and maintainable
- **Unit Testing:** planned for all modules (including error cases)
- **main.py:** upcoming module to orchestrate all pipeline steps in a single execution
- **Limitations:** processing time can be significant; tree detection quality varies