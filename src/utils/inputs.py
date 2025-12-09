from dataclasses import dataclass
from enum import Enum

class RoutingPreference(Enum):
    SHORTEST = "length"
    GREENEST = "weight"

@dataclass
class UserInput:
    aoi_name: object
    sw_lat: object
    sw_lon: object
    ne_lat: object
    ne_lon: object
    resolution: object
    routing_source: object = None
    routing_target: object = None
    routing_weight: RoutingPreference = RoutingPreference.GREENEST

def user_input():
    # USER INPUT:
    # SW and NE coordinates (lon, lat)
    # Resolution (min: 0.6 meter/pixel is the highest possible in NAIP)
    aoi_name = "bend_oregon"
    sw_lat, sw_lon = 44.05, -121.3285
    ne_lat, ne_lon = 44.06, -121.3145
    resolution = 0.6

    # USER ROUTING INPUT:
    # Source, target, weight
    routing_source = 4359644597
    routing_target = 5106302551
    routing_weight = RoutingPreference.SHORTEST #Choose GREENEST or SHORTEST

    return UserInput(
        aoi_name = aoi_name,
        sw_lat = sw_lat,
        sw_lon = sw_lon,
        ne_lat = ne_lat,
        ne_lon = ne_lon,
        resolution = resolution,
        routing_source = routing_source,
        routing_target = routing_target,
        routing_weight = routing_weight
        )