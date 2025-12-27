import pytest
from unittest.mock import patch
import os
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from utils.inputs import UserInput, RoutingPreference
from utils.geometry import (
    BoundingBoxMercator,
    bounding_box_mercator,
    tile_calculator,
    bounding_box_osm,
    reproject_raster_layer)

"""
Tests for utils.geometry

Function tested: bounding_box_mercator(user_input)
- Converts WGS84 lat/lon to EPSG:3857 Mercator
- Returns BoundingBoxMercator

Test categories:
- Normal cases: typical valid coordinates
- Edge cases: extreme lat/lon (poles, dateline)
"""

def test_bounding_box_mercator_normal_coordinates():
    """
    Typical valid coordinates (SW < NE)
    Verify:
    - Returned object is BoundingBoxMercator
    - xmin < xmax, ymin < ymax
    - Rough numeric check of expected transformed coordinates
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = 0,
        sw_lon = 0,
        ne_lat = 1,
        ne_lon = 1,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_mercator = bounding_box_mercator(user_input)

    assert isinstance(bbox_mercator, BoundingBoxMercator)

    assert bbox_mercator.xmin < bbox_mercator.xmax
    assert bbox_mercator.ymin < bbox_mercator.ymax

    assert bbox_mercator.xmin == 0
    assert bbox_mercator.ymin == 0
    assert 111000 < bbox_mercator.xmax < 112000
    assert 111000 < bbox_mercator.ymax < 112000

def test_bounding_box_mercator_extreme_coordinates():
    """
    Extreme lat/lon values
    Verify:
    - Returned object is BoundingBoxMercator
    - xmin < xmax, ymin < ymax
    - No infinite values
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = -85,
        sw_lon = -179,
        ne_lat = 85,
        ne_lon = 179,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_mercator = bounding_box_mercator(user_input)

    assert isinstance(bbox_mercator, BoundingBoxMercator)

    assert bbox_mercator.xmin < bbox_mercator.xmax
    assert bbox_mercator.ymin < bbox_mercator.ymax

    for val in [bbox_mercator.xmin, bbox_mercator.ymin, bbox_mercator.xmax, bbox_mercator.ymax]:
        assert val != float("inf")

def test_tile_calculator_normal_bbox():
    """
    Typical bounding box and resolution.

    Verify:
    - Returned width and height are integers
    - Width and height are computed correctly from bbox size and resolution
    """
    bbox_mercator = BoundingBoxMercator(
        xmin = 0,
        ymin = 0,
        xmax = 10,
        ymax = 10)
    resolution = 1

    width, height = tile_calculator(bbox_mercator, resolution)

    assert isinstance(width, int)
    assert isinstance(height, int)

    assert width == 10
    assert height == 10


@pytest.mark.parametrize(
    "xmax, ymax, expected_msg",
        [
            (0.1,0.1,"Width and height (pixel count) must be >= 1. Width: 0, height: 0"),
            (10000,10000, "Tile size too large: maximum allowed is 2500x2500 pixels. Width: 10000, height: 10000")
        ]
)
def test_tile_calculator_invalid_bbox_size(xmax, ymax, expected_msg):
    """
    Invalid bounding box sizes resulting in unusable tile dimensions.

    Verify:
    - A ValueError is raised when the resulting width or height is < 1 pixel
    - A ValueError is raised when the resulting width or height exceeds the maximum allowed size (2500*2500 pixels)
    - The error message matches the expected, user-facing message
    - Resolution constraints (minimum 0.6m for NAIP imagery) are validated upstream and are not tested here
    """
    bbox_mercator = BoundingBoxMercator(
            xmin = 0,
            ymin = 0,
            xmax = xmax,
            ymax = ymax)

    resolution = 1

    with pytest.raises(ValueError) as exc_info:
        tile_calculator(bbox_mercator, resolution)

    assert str(exc_info.value) == expected_msg

def test_bounding_box_osm_normal_coordinates():
    """
    Normal bounding box coordinates converted to an OSM-compatible tuple.

    Verify:
    - The returned object is a tuple
    - All values are floats
    - The ordering is correct: (xmin, ymin, xmax, ymax)
    - Typical SW < NE coordinates are handled correctly
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = 0,
        sw_lon = 0,
        ne_lat = 1,
        ne_lon = 1,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_osm = bounding_box_osm(user_input)

    assert isinstance(bbox_osm, tuple)

    for val in bbox_osm:
        assert isinstance(val, float)
    
    assert bbox_osm == (user_input.sw_lon, user_input.sw_lat, user_input.ne_lon, user_input.ne_lat)

def test_bounding_box_osm_extreme_coordinates():
    """
    Extreme bounding box coordinates converted to an OSM-compatible tuple.

    Verify:
    - The returned object is a tuple
    - xmin < xmax, ymin < ymax
    - No value is infinite
    - Works with coordinates near valid extremes (-85 to 85 latitude, -179 to 179 longitude)
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = -85,
        sw_lon = -179,
        ne_lat = 85,
        ne_lon = 179,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_osm = bounding_box_osm(user_input)

    assert isinstance(bbox_osm, tuple)

    assert bbox_osm[0] < bbox_osm[2]
    assert bbox_osm[1] < bbox_osm[3]

    for val in bbox_osm:
        assert val != float("inf")
        assert isinstance(val, float)

@pytest.fixture
def simple_raster(tmp_path):
    """
    Create a simple 1-band 10x10 raster with EPSG:4326 CRS for testing.

    Returns:
        Path: Path to the created raster file.
    """
    raster_path = tmp_path / "input.tif"

    data = np.ones((1, 10, 10), dtype=np.uint8)
    transform = from_origin(0, 10, 1, 1)  # top left corner is at: x=0,y=10, pixel size=1

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)

    return raster_path

def test_reproject_raster_layer_creates_output(simple_raster, tmp_path):
    """
    Reproject a valid single-band raster to a target CRS and write the result to disk.

    Verify:
    - The output raster file is created
    - The output raster CRS matches the requested target CRS
    - The output raster has valid, non-zero dimensions
    - The number of bands is preserved from the input raster
    """
    dst_crs = 'EPSG:5070'
    output_raster = tmp_path / "output.tif"

    reproject_raster_layer(dst_crs, simple_raster, output_raster)

    assert output_raster.exists()

    with rasterio.open(output_raster) as dst:
        assert dst.crs.to_string() == dst_crs
        assert dst.width > 0
        assert dst.height > 0
        assert dst.count == 1 #1band

def test_reproject_raster_layer_missing_input(tmp_path):
    """
    Verify that reprojecting a raster with a missing input path raises a RasterioIOError.
    """
    input_raster = tmp_path / "missing.tif"
    output_raster = tmp_path / "output.tif"

    with pytest.raises(rasterio.errors.RasterioIOError):
        reproject_raster_layer('EPSG:5070', input_raster, output_raster)

def test_reproject_raster_layer_invalid_crs(simple_raster, tmp_path):
    """
    Verify that reprojecting a raster with an invalid CRS string
    raises an error (ValueError or CRSError depending on rasterio version).
    """
    output_raster = tmp_path / "output.tif"

    with pytest.raises((rasterio.errors.CRSError, ValueError)):
        reproject_raster_layer('EPSG:INVALID', simple_raster, output_raster)

def test_reproject_raster_layer_permission_denied(simple_raster, tmp_path):
    """
    Verify that attempting to write to a location with simulated permission denial raises a RasterioIOError.
    """
    output_raster = tmp_path / "no_write"

    with patch("rasterio.open", side_effect=rasterio.errors.RasterioIOError("Permission denied")):
        with pytest.raises(rasterio.errors.RasterioIOError):
            reproject_raster_layer('EPSG:5070', simple_raster, output_raster)


"""
----------------------------------------
Function: reproject_vector_layer(dst_crs, input_vector, output_vector)
----------------------------------------
# Normal cases
# - Small GeoDataFrame -> output file created
# - Verify CRS of output

# Edge cases
# - Empty GeoDataFrame
# - Invalid CRS string

# Error cases
# - input_vector path does not exist -> FileNotFoundError
# - output_vector path permission denied -> PermissionError

----------------------------------------
Function: raster_to_vector(input_raster_path, output_vector_path)
----------------------------------------
# Normal cases
# - Small raster mask with 255 pixels -> vector polygons created
# - Output file created

# Edge cases
# - Raster with no 255 pixels -> output GeoDataFrame empty
# - Single pixel raster -> produces single polygon
# - Large raster -> memory usage reasonable (can mock)

# Error cases
# - Input file does not exist -> FileNotFoundError
# - Output path permission denied -> PermissionError

----------------------------------------
Function: add_id(gdf, id_vector_path)
----------------------------------------
# Normal cases
# - GeoDataFrame with multiple features -> 'id' column added, starts at 1

# Edge cases
# - Empty GeoDataFrame -> 'id' column added (empty)
# - Existing 'id' column -> should overwrite or handle gracefully

# Error cases
# - Output path permission denied -> PermissionError

----------------------------------------
Function: buffer_vector(gdf, distance)
----------------------------------------
# Normal cases
# - Typical polygon -> buffered correctly
# - Line or point geometries -> buffered correctly

# Edge cases
# - Distance = 0 -> geometries unchanged
# - Negative distance -> optional behavior
# - Empty GeoDataFrame

# Error cases
# - Invalid geometry types -> should raise error

----------------------------------------
Function: clipping_vectors(input_vector, mask_vector, output_vector_path)
----------------------------------------
# Normal cases
# - Input polygon clipped by mask -> output matches expected
# - Output file created

# Edge cases
# - Input or mask empty -> output empty
# - No overlap between input and mask -> output empty
# - Partial overlap -> check geometry

# Error cases
# - Output path permission denied -> PermissionError

----------------------------------------
Function: calculate_area(gdf)
----------------------------------------
# Normal cases
# - Polygon geometries -> 'area' column added, positive values
# - Multipolygons -> areas sum correctly

# Edge cases
# - Empty GeoDataFrame -> 'area' column added (empty)
# - Degenerate polygons -> area = 0
# - Polygons with invalid geometries -> handled or fixed

# Error cases
# - Non-polygon geometries -> should raise error or skip

----------------------------------------
Function: join_by_attribute(gdf, join)
----------------------------------------
# Normal cases
# - Matching IDs -> area values merged
# - Non-matching IDs -> NaN or filled value

# Edge cases
# - Empty gdf or join -> returns empty or unchanged
# - Duplicate IDs in join -> behavior defined (merge strategy)

# Error cases
# - Missing 'id' column -> KeyError

----------------------------------------
Function: calculate_greendex(gdf)
----------------------------------------
# Normal cases
# - Normal area_x, area_y values -> greendex and weight calculated
# - Length normalization correct

# Edge cases
# - area_x = 0 -> greendex = 0
# - area_y > area_x -> greendex > 1 -> capped or handled
# - length min == max -> division by zero

# Error cases
# - Missing columns -> KeyError
# - Empty GeoDataFrame
"""
