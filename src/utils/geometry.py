from dataclasses import dataclass
from pyproj import Transformer
from utils.inputs import user_input, UserInput
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from rasterio.warp import calculate_default_transform, reproject, Resampling


@dataclass
class BoundingBoxMercator:
    xmin: object
    ymin: object
    xmax: object
    ymax: object

def bounding_box_mercator(user_input: UserInput):
    # This function transforms a two WGS84 (lat-long) coordinate pairs to Web Mercator

    sw_lon = user_input.sw_lon
    sw_lat = user_input.sw_lat
    ne_lon = user_input.ne_lon
    ne_lat = user_input.ne_lat

    # Transform from WGS84 to Web Mercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    # Transformation done here
    xmin, ymin = transformer.transform(sw_lon, sw_lat)
    xmax, ymax = transformer.transform(ne_lon, ne_lat)

    return BoundingBoxMercator(
        xmin = xmin, 
        ymin = ymin,
        xmax = xmax,
        ymax = ymax)

def tile_calculator(bbox_mercator: BoundingBoxMercator, resolution):
    # This function calculates width and height required for the NAIP request

    xmin = bbox_mercator.xmin
    ymin = bbox_mercator.ymin
    xmax = bbox_mercator.xmax
    ymax = bbox_mercator.ymax

    width  = int(round((xmax - xmin) / resolution))
    height = int(round((ymax - ymin) / resolution))
    print('Width: ', width)
    print('Height: ', height)
 
    return width, height

def bounding_box_osm(user_input: UserInput):

    xmin = user_input.sw_lon
    ymin = user_input.sw_lat
    xmax = user_input.ne_lon
    ymax = user_input.ne_lat

    # OSM requires WGS84 bbox as tuple: left, bottom, right, top
    bbox_osm = (xmin, ymin, xmax, ymax)
    print("bbox: ", bbox_osm)
    return bbox_osm

def reproject_raster_layer(dst_crs, input_raster, output_raster):
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

def reproject_vector_layer(dst_crs, input_vector, output_vector):
    gdf = gpd.read_file(input_vector)
    gdf = gdf.to_crs(dst_crs)
    gdf.to_file(output_vector, driver="GPKG")

def raster_to_vector(input_raster_path, output_vector_path):
    # Input: input raster path,output vector path
    # Saves intermediate geopackage with tree features
    with rasterio.open(input_raster_path) as src:
        features = []
        for geom, value in shapes(src.read(1), transform=src.transform):
            if value == 255:
                features.append({
                    "geometry": shape(geom), "value": value})
    
        gdf = gpd.GeoDataFrame(features, crs=src.crs)
        gdf.to_file(output_vector_path, driver="GPKG")

def dissolve_vector(input_vector):
    # Input: input vector geodataframe
    # Returns a geodataframe with dissolved features 
    dissolved = input_vector.copy()
    dissolved = dissolved.dissolve(by=None, method='coverage')
    return dissolved

def simplify_vector(dissolved, tolerance):
    # Input: geodataframe from the dissolve_vector() function
    # Returns a geodataframe with simplified geometries
    simplified = dissolved.copy()
    simplified.geometry = simplified.geometry.simplify(tolerance, preserve_topology=True)
    return simplified

def buffer_vector(simplified, distance):
    # Input: geodataframe e.g. from the simplify_vector() function
    # Returns a geodataframe with buffered geometries 
    buffered = simplified.copy()
    buffered.geometry = buffered.geometry.buffer(distance)
    return buffered