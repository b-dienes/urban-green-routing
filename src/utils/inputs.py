from dataclasses import dataclass

@dataclass
class UserInput:
    sw_lat: object
    sw_lon: object
    ne_lat: object
    ne_lon: object
    resolution: object

def user_input():
    # USER INPUT:
    # SW and NE coordinates (lon, lat)
    # Resolution (min: 0.6 meter/pixel is the highest possible in NAIP)
    sw_lat, sw_lon = 44.05, -121.3285
    ne_lat, ne_lon = 44.06, -121.3145
    resolution = 0.6

    return UserInput(
        sw_lat = sw_lat,
        sw_lon = sw_lon,
        ne_lat = ne_lat,
        ne_lon = ne_lon,
        resolution = resolution)