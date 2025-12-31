"""
Geometry utilities for performing geospatial coordinate transformations,
tiling calculations, and other spatial processing steps used in the pipeline.
"""

import logging
from pathlib import Path
from dataclasses import dataclass
from pyproj import Transformer
from utils.inputs import user_input, UserInput
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from rasterio.warp import calculate_default_transform, reproject, Resampling


logger = logging.getLogger(__name__)

@dataclass
class BoundingBoxMercator:
    """
    Web Mercator representation of a geographic bounding box.
    Stores projected xmin, ymin, xmax, ymax coordinates in meters.
    """
    xmin: float
    ymin: float
    xmax: float
    ymax: float

def bounding_box_mercator(user_input: UserInput) -> BoundingBoxMercator:
    """
    Convert user-defined WGS84 bounding box into Web Mercator coordinates.

    Parameters:
        user_input (UserInput): User-provided spatial extent and parameters.

    Returns:
        BoundingBoxMercator: Bounding box in EPSG:3857 (Web Mercator).
    """

    sw_lon = user_input.sw_lon
    sw_lat = user_input.sw_lat
    ne_lon = user_input.ne_lon
    ne_lat = user_input.ne_lat

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    xmin, ymin = transformer.transform(sw_lon, sw_lat)
    xmax, ymax = transformer.transform(ne_lon, ne_lat)

    return BoundingBoxMercator(
        xmin = xmin, 
        ymin = ymin,
        xmax = xmax,
        ymax = ymax)

def tile_calculator(bbox_mercator: BoundingBoxMercator, resolution: float) -> tuple[int, int]:
    """
    Compute output raster width and height (in pixels) from a
    Web Mercator bounding box and a target spatial resolution.

    Parameters:
        bbox_mercator (BoundingBoxMercator): Bounding box in EPSG:3857.
        resolution (float): Target resolution in meters per pixel.

    Returns:
        Tuple[int, int]: (width, height) in pixels.
    """

    xmin = bbox_mercator.xmin
    ymin = bbox_mercator.ymin
    xmax = bbox_mercator.xmax
    ymax = bbox_mercator.ymax

    width  = int(round((xmax - xmin) / resolution))
    height = int(round((ymax - ymin) / resolution))

    if width < 1 or height < 1:
        raise ValueError(
            f"Width and height (pixel count) must be >= 1. "
            f"Width: {width}, height: {height}")

    if width >2500 or height > 2500:
        raise ValueError(
            f"Tile size too large: maximum allowed is 2500x2500 pixels. "
            f"Width: {width}, height: {height}")

    logger.info("Width: %d", width)
    logger.info("Height: %d", height) 

    return width, height

def bounding_box_osm(user_input: UserInput) -> tuple[float, float, float, float]:
    """
    Construct an OpenStreetMap-compatible bounding box (WGS84) from user input.

    Parameters:
        user_input (UserInput): Object containing AOI coordinates (southwest and northeast corners).

    Returns:
        tuple[float, float, float, float]: Bounding box in the form (xmin, ymin, xmax, ymax)
                                           corresponding to (left, bottom, right, top).
    """

    xmin = user_input.sw_lon
    ymin = user_input.sw_lat
    xmax = user_input.ne_lon
    ymax = user_input.ne_lat

    bbox_osm = (float(xmin), float(ymin), float(xmax), float(ymax))
    logger.info("OSM bounding box (WGS84): West: %s, South: %s, East: %s, North: %s", xmin, ymin, xmax, ymax)
    return bbox_osm

def reproject_raster_layer(dst_crs: str, input_raster: Path, output_raster: Path) -> None:
    """
    Reproject a raster to a target CRS and save the output as a new file.

    Parameters:
        dst_crs (str): Target coordinate reference system (e.g. 'EPSG:5070').
        input_raster (Path): Path to the input raster file.
        output_raster (Path): Path where the reprojected raster will be saved.

    Returns:
        None
    """
    with rasterio.open(input_raster) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height})

        with rasterio.open(output_raster, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

def reproject_vector_layer(dst_crs: str, input_vector: Path, output_vector: Path) -> None:
    """
    Reproject a vector file (GeoPackage) to a target CRS and save the output.

    Parameters:
        dst_crs (str): Target coordinate reference system (e.g. 'EPSG:5070').
        input_vector (Path): Path to the input vector file.
        output_vector (Path): Path where the reprojected vector will be saved.

    Returns:
        None
    """
    gdf = gpd.read_file(input_vector)
    gdf = gdf.to_crs(dst_crs)
    gdf.to_file(output_vector, driver="GPKG")

def raster_to_vector(input_raster_path: Path, output_vector_path: Path) -> None:
    """
    Convert a binary raster mask into vector polygons and save them as a GeoPackage.

    Pixels with a grayscale value of 255 are extracted and converted to vector
    geometries. All other pixel values are ignored.

    Parameters:
        input_raster_path (Path): Path to the input raster mask file.
        output_vector_path (Path): Path where the output vector file will be saved.

    Raises:
        ValueError: If no foreground pixels (value=255) are found in the input raster.

    Returns:
        None
    """
    with rasterio.open(input_raster_path) as src:
        features = []
        for geom, value in shapes(src.read(1), transform=src.transform):
            if value == 255:
                features.append({
                    "geometry": shape(geom), "value": value})

        if not features:
            raise ValueError("No foreground pixels (value=255) found in raster")

        gdf = gpd.GeoDataFrame(features, crs=src.crs)
        gdf.to_file(output_vector_path, driver="GPKG")

def add_id(gdf: gpd.GeoDataFrame, id_vector_path: Path) -> gpd.GeoDataFrame:
    """
    Add a unique integer ID column to a GeoDataFrame and save the result.

    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame.
        id_vector_path (Path): Path where the GeoDataFrame with IDs will be saved.

    Returns:
        GeoDataFrame: GeoDataFrame with an added unique 'id' column.
    """
    gdf = gdf.copy()
    gdf['id'] = range(1, len(gdf)+1)
    gdf.to_file(id_vector_path, driver="GPKG")
    return gdf

def buffer_vector(gdf: gpd.GeoDataFrame, distance: float) -> gpd.GeoDataFrame:
    """
    Create buffer geometries around input vector features.
    Notes:
        The buffer distance is interpreted in the units of the GeoDataFrame's CRS.
        A projected (metric) CRS is recommended for meaningful buffer distances,
        but the operation will still execute for geographic CRSs (e.g. EPSG:4326)
        without raising an error.

    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame containing geometries to buffer.
        distance (float): Buffer distance in CRS units.

    Raises:
        ValueError: If the buffer distance is zero or negative.
        ValueError: If the input GeoDataFrame contains null geometries.
        ValueError: If the input GeoDataFrame contains invalid geometries.

    Returns:
        GeoDataFrame: GeoDataFrame with buffered geometries.
    """
    if distance <= 0:
        raise ValueError("Invalid buffer distance")
    
    if gdf.empty:
        return gdf.copy()

    if not gdf.geometry.notnull().all():
        raise ValueError("Input contains null geometries")

    if not gdf.geometry.is_valid.all():
        raise ValueError("Input contains invalid geometries")

    buffered = gdf.copy()
    buffered.geometry = buffered.geometry.buffer(distance)
    return buffered

def clipping_vectors(input_vector: gpd.GeoDataFrame, mask_vector: gpd.GeoDataFrame, output_vector_path: Path) -> None:
    """
    Clip input vector geometries using a mask vector and save the result.

    Parameters:
        input_vector (GeoDataFrame): GeoDataFrame containing features to be clipped.
        mask_vector (GeoDataFrame): GeoDataFrame used as the clipping mask.
        output_vector_path (Path): Path where the clipped vector file will be saved.

    Raises:
        ValueError: If the input and mask GeoDataFrames have different CRS.
        ValueError: If the input or mask GeoDataFrame contains null geometries.
        ValueError: If the input or mask GeoDataFrame contains invalid geometries.

    Returns:
        None
    """
    if input_vector.crs != mask_vector.crs:
        raise ValueError("Input and mask CRS must match")

    if not input_vector.geometry.notnull().all():
        raise ValueError("Input contains null geometries")

    if not mask_vector.geometry.notnull().all():
        raise ValueError("Mask contains null geometries")

    if not input_vector.geometry.is_valid.all():
        raise ValueError("Input contains invalid geometries")

    if not mask_vector.geometry.is_valid.all():
        raise ValueError("Mask contains invalid geometries")

    clipped = gpd.clip(input_vector, mask_vector, keep_geom_type=False, sort=False)
    clipped.to_file(output_vector_path, driver="GPKG")

def calculate_area(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate polygon areas and store them in a new 'area' column.

    Any missing or invalid area values are replaced with 0 to ensure
    downstream calculations remain valid.

    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame with polygon geometries.

    Raises:
        ValueError: If the input GeoDataFrame contains null geometries.
        ValueError: If the input GeoDataFrame contains invalid geometries.

    Returns:
        GeoDataFrame: GeoDataFrame with an added 'area' column.
    """
    if not gdf.geometry.notnull().all():
        raise ValueError("Input contains null geometries")

    if not gdf.geometry.is_valid.all():
        raise ValueError("Input contains invalid geometries")

    aread = gdf.copy()
    aread['area'] = aread.geometry.area
    aread['area'] = aread['area'].fillna(0)
    return aread

def join_by_attribute(gdf: gpd.GeoDataFrame, join: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Join area attributes from another GeoDataFrame based on a shared ID field.

    Parameters:
        gdf (GeoDataFrame): Target GeoDataFrame.
        join (GeoDataFrame): GeoDataFrame containing 'id' and 'area' columns.

    Raises:
        ValueError: If the input GeoDataFrame is missing the 'id' column.
        ValueError: If the join GeoDataFrame is missing the 'id' column.

    Returns:
        GeoDataFrame: GeoDataFrame with joined area attributes.
    """
    if 'id' not in gdf.columns:
        raise ValueError("ID field is missing in input layer: add 'id'")

    if 'id' not in join.columns:
        raise ValueError("ID field is missing in join layer: add 'id'")

    joined = gdf.merge(join[['id','area']], on='id', how='left')
    return joined

def calculate_greendex(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Compute greendex and weight metrics for road segments based on green coverage.

    Greendex is calculated as the ratio of tree-covered buffer area to total
    road buffer area. Missing greendex values are replaced with 0.

    Segment length is normalized to the range [0, 1].
    
    Greendex is inverted (1 - greendex) so that both metrics share the same directionality:
    0 represents best conditions and 1 represents worst conditions.

    Weight is computed as the product of normalized segment length and inverted greendex.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame containing area and length attributes.

    Returns:
        GeoDataFrame: GeoDataFrame with added 'greendex' and 'weight' columns.
    """
    gdf['greendex'] = gdf['area_y'] / gdf['area_x']
    gdf['greendex'] = gdf['greendex'].fillna(0)
    gdf['greendex'] = gdf['greendex'].round(4)

    length_norm = (gdf['length'] - gdf['length'].min()) / (gdf['length'].max() - gdf['length'].min())
    green_norm = 1 - gdf['greendex']
    gdf['weight'] = length_norm * green_norm
    gdf['weight'] = gdf['weight'].round(4)

    return gdf