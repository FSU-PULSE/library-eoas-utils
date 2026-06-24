"""Great-circle distance utilities for point pairs and regular lat-lon grids."""

import numpy as np

_EARTH_RADIUS_M = 6371000


def haversine(p1: np.ndarray, p2: np.ndarray) -> float:
    """Compute great-circle distance between two points on Earth.

    Uses the haversine formula with a spherical Earth approximation.

    Args:
        p1: First point as ``[lat_deg, lon_deg]``.
        p2: Second point as ``[lat_deg, lon_deg]``.

    Returns:
        Distance in meters.

    Assumptions:
        Earth radius is fixed at 6_371_000 m. Inputs are decimal degrees.
    """
    p1, p2 = map(np.radians, [p1, p2])

    dlat = p1[0] - p2[0]
    dlon = p1[1] - p2[1]

    a = np.sin(dlat / 2.0) ** 2 + np.cos(p1[0]) * np.cos(p2[0]) * np.sin(dlon / 2.0) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    dist = _EARTH_RADIUS_M * c
    return dist


def haversineForGrid(grid: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Compute cell-edge distances on a 2-D lat-lon meshgrid.

    Args:
        grid: Tuple ``(lon_grid, lat_grid)`` from ``numpy.meshgrid``, each with
            shape ``(n_lat, n_lon)``.

    Returns:
        Array with shape ``(2, n_lat - 1, n_lon - 1)`` in meters.
        Index ``0`` holds meridional (latitude) edge lengths; index ``1`` holds
        zonal (longitude) edge lengths between adjacent grid nodes.

    Assumptions:
        Grid spacing follows the ordering produced by ``meshgrid(lons, lats)``.
    """
    lon_rad = np.radians(grid[0])
    lat_rad = np.radians(grid[1])

    dlat = lat_rad[1:, :] - lat_rad[:-1, :]
    dlon = lon_rad[:, 1:] - lon_rad[:, :-1]

    out_dims = (2, grid[0].shape[0] - 1, grid[0].shape[1] - 1)
    output = np.zeros(out_dims)

    # output[0] holds vertical distance (based on dlat)
    output[0, :, :] = np.sin(dlat[:, :-1] / 2.0) ** 2
    # output[1] holds horizontal distance (based on dlon)
    output[1, :, :] = (
        np.cos(lat_rad[:-1, 1:])
        * np.cos(lat_rad[:-1, :-1])
        * np.sin(dlon[:-1, :] / 2.0) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(output))
    dist = _EARTH_RADIUS_M * c
    return dist


def get_ccrs_bbox(lats: np.ndarray, lons: np.ndarray) -> tuple:
    """Return a Cartopy-style bounding box from coordinate arrays.

    Args:
        lats: Latitude values in decimal degrees.
        lons: Longitude values in decimal degrees.

    Returns:
        Tuple ``(min_lon, max_lon, min_lat, max_lat)``.
    """
    return (np.amin(lons), np.amax(lons), np.amin(lats), np.amax(lats))


if __name__ == "__main__":

    # ------ For two points
    # p1 = [0, 0]
    # p2 = [0, 1]
    # d = haversine(p1, p2)
    # print(F"Distance between {p1}(lat,lon) and {p2}(lat,lon) is {d:.3f} m")

    # ------ For grid
    lat = np.linspace(-10, 10, 21)
    lon = np.linspace(-20, 20, 41)
    grid = np.meshgrid(lon, lat)
