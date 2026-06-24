import numpy as np
import pytest
from proc_utils.geometries import intersect_polygon_grid, histogram_from_locations
from proc_utils.proj import haversineForGrid

def test_intersect_polygon_grid():
    grid = np.zeros((10, 10))
    lats = np.linspace(0, 9, 10)
    lons = np.linspace(0, 9, 10)
    # A polygon enclosing the region [2, 5] x [2, 5]
    geo_poly = [[2, 2], [5, 2], [5, 5], [2, 5], [2, 2]]
    
    updated_grid = intersect_polygon_grid(grid.copy(), lats, lons, geo_poly, value=2)
    # Check that points inside are updated
    assert updated_grid[3, 3] == 2
    # Check that points outside are not updated
    assert updated_grid[1, 1] == 0
    assert updated_grid[6, 6] == 0

def test_histogram_from_locations():
    grid = np.zeros((5, 5))
    lats = np.array([10, 20, 30, 40, 50])
    lons = np.array([10, 20, 30, 40, 50])
    locations = [
        [15, 15],  # falls between 10 and 20 -> idx_i = 0, idx_j = 0
        [25, 35],  # falls between 20 and 30 (lat), 30 and 40 (lon) -> idx_i = 1, idx_j = 2
        [25, 35],  # duplicate coordinate to test accumulation
        [55, 55],  # out of bounds coordinate, should be skipped safely
    ]
    updated_grid = histogram_from_locations(grid.copy(), lats, lons, locations)
    assert updated_grid[0, 0] == 1
    assert updated_grid[1, 2] == 2
    assert updated_grid[4, 4] == 0

def test_haversineForGrid():
    lons = np.linspace(-10, 10, 5)
    lats = np.linspace(-10, 10, 5)
    grid = np.meshgrid(lons, lats)
    
    dist = haversineForGrid(grid)
    # Shape must be (2, H-1, W-1) which is (2, 4, 4)
    assert dist.shape == (2, 4, 4)
    assert np.all(dist >= 0)
