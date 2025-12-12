"""
Provides the user-defined configuration for the routing workflow.
Defines routing preferences, the UserInput dataclass, and a function
to construct the initial user input object used throughout the project.
"""

import logging
from dataclasses import dataclass
from enum import Enum


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

class RoutingPreference(Enum):
    """Available routing optimization modes."""
    SHORTEST = "length"
    GREENEST = "weight"

@dataclass
class UserInput:
    """Container for all user-provided parameters controlling the pipeline."""
    aoi_name: str
    sw_lat: float
    sw_lon: float
    ne_lat: float
    ne_lon: float
    resolution: float
    routing_source: int | None = None
    routing_target: int | None = None
    routing_weight: RoutingPreference = RoutingPreference.GREENEST

def user_input() -> UserInput:
    """
    Build and return the UserInput configuration for the routing workflow.
    """
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

    logger.info("User input created: %s", aoi_name)

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