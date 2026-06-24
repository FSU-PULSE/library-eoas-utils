"""Spatial masking and histogram accumulation on regular lat-lon grids."""

import numpy as np
from matplotlib import path


def intersect_polygon_grid(
    grid: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    geo_poly: np.ndarray,
    value: float = 1,
) -> np.ndarray:
    """Increment grid cells whose centers fall inside a geographic polygon.

    Args:
        grid: 2-D array, shape ``(n_lat, n_lon)``. Modified in place and also
            returned.
        lats: 1-D latitude coordinates, length ``n_lat``.
        lons: 1-D longitude coordinates, length ``n_lon``.
        geo_poly: Polygon vertices with shape ``(n_vertices, 2)`` as
            ``[lon, lat]`` pairs (matplotlib ``Path`` convention).
        value: Scalar added at masked cells where ``grid`` is not NaN.

    Returns:
        Updated ``grid`` array.

    Assumptions:
        Grid nodes are interpreted at cell centers via ``meshgrid(lons, lats)``.
        NaN cells are skipped and never incremented.
    """
    gom_path = path.Path(geo_poly)

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    points = np.vstack((lon_grid.ravel(), lat_grid.ravel())).T

    mask = gom_path.contains_points(points).reshape(grid.shape)

    valid = ~np.isnan(grid)
    grid[valid & mask] += value

    return grid


def histogram_from_locations(
    grid: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    locations: np.ndarray,
) -> np.ndarray:
    """Accumulate point counts into a 2-D lat-lon histogram grid.

    Args:
        grid: 2-D count array, shape ``(n_lat, n_lon)``. Modified in place.
        lats: 1-D sorted latitude bin edges, length ``n_lat``.
        lons: 1-D sorted longitude bin edges, length ``n_lon``.
        locations: Point coordinates with shape ``(N, 2)``. Column 0 is matched
            against ``lats`` and column 1 against ``lons``.

    Returns:
        Updated ``grid`` with +1 added at each valid bin.

    Assumptions:
        Bin assignment uses ``numpy.digitize(..., right=True)`` so a point at
        coordinate ``x`` falls in the bin where ``bins[i-1] < x <= bins[i]``.
        Points outside ``[lats[0], lats[-1])`` or ``[lons[0], lons[-1])`` are
        discarded.

    TODO:
        Clarify whether ``locations`` are always geographic ``(lat, lon)`` or
        can be ``(row, col)`` indices as the legacy docstring suggested.
    """
    if len(locations) == 0:
        return grid

    locations = np.asarray(locations)
    rows = locations[:, 0]
    cols = locations[:, 1]

    idx_i = np.digitize(rows, lats, right=True) - 1
    idx_j = np.digitize(cols, lons, right=True) - 1

    valid = (idx_i >= 0) & (idx_i < len(lats) - 1) & (idx_j >= 0) & (idx_j < len(lons) - 1)
    idx_i = idx_i[valid]
    idx_j = idx_j[valid]

    np.add.at(grid, (idx_i, idx_j), 1)

    return grid
