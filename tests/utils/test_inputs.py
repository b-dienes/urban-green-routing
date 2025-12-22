import pytest
from utils.inputs import UserInput, RoutingPreference

"""
Tests for utils.inputs

Function tested: UserInput dataclass
- Stores user-provided AOI and coordinate information
- Performs validation on construction

Test categories:
- Normal cases: valid coordinates, all fields provided
- Edge/error cases: 
    * SW > NE coordinates
    * Degenerate bounding box (SW == NE)
    * Missing critical fields
    * Extreme latitude/longitude values
"""

@pytest.mark.parametrize(
    "sw_lat, sw_lon, ne_lat, ne_lon, expected_msg",
        [
            (1,1,0,0,"SW coordinates must be smaller than NE coordinates"),
            (None, None, None, None, "Missing required user input fields"),
            (0,0,91,1,"Latitude must be between -90 and 90"),
            (0,0,1,181,"Longitude must be between -180 and 180"),
            (1,1,1,1,"Degenerate bounding box: SW and NE cannot be equal")
        ]
)
def test_user_input_invalid_construction(sw_lat, sw_lon, ne_lat, ne_lon, expected_msg):
        """
        Test that invalid UserInput values raise the correct ValueError.
        
        Parameters are passed via pytest parametrize:
        - sw_lat, sw_lon, ne_lat, ne_lon: coordinates
        - expected_msg: expected ValueError message
        """
        with pytest.raises(ValueError, match=expected_msg):
            user_input = UserInput(
            aoi_name = "test_aoi",
            sw_lat = sw_lat,
            sw_lon = sw_lon,
            ne_lat = ne_lat,
            ne_lon = ne_lon,
            resolution = 1,
            routing_source = 1,
            routing_target = 2,
            routing_weight = RoutingPreference.SHORTEST)

def test_user_input_valid_construction():
    """
    Test that UserInput can be created with valid coordinates and does not raise any exceptions.
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
