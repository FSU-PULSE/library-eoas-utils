"""Derived oceanographic fields from velocity components."""

import numpy as np
from proc_utils.proj import haversine


def coriolis(lats: np.ndarray) -> np.ndarray:
    """Compute the Coriolis parameter for a latitude array.

    Uses :math:`f = 2 \\Omega \\sin(\\phi)` with
    :math:`\\Omega = 2\\pi / (24 \\cdot 3600)` rad/s.

    Args:
        lats: Latitude values in decimal degrees. Any broadcastable shape.

    Returns:
        Coriolis parameter :math:`f` in s\\ :sup:`-1`, same shape as ``lats``.

    Assumptions:
        Earth rotation period is exactly 24 hours (no leap-second correction).
    """
    omeg = 2 * np.pi / (24 * 3600)
    f = 2 * omeg * np.sin(np.deg2rad(lats))
    return f


def vorticity(
    u: np.ndarray, v: np.ndarray, dist_grid: np.ndarray | None = None
) -> np.ndarray:
    """Compute relative vorticity from zonal and meridional velocity.

    For 2-D fields the discrete estimate is
    :math:`\\zeta \\approx \\partial v/\\partial x - \\partial u/\\partial y`.
    When ``dist_grid`` is provided, finite differences are divided by edge
    lengths in meters (see :func:`proc_utils.proj.haversineForGrid`).

    Args:
        u: Zonal velocity component. Supported shapes:
            ``(lat, lon)``, ``(time, lat, lon)``, or ``(time, depth, lat, lon)``.
        v: Meridional velocity component, same shape as ``u``.
        dist_grid: Optional distance array with shape ``(2, n_lat-1, n_lon-1)``
            giving meridional and zonal grid spacing in meters.

    Returns:
        Vorticity array with the same rank as ``u``. Interior stencil values are
        filled; outer rows/columns remain zero.

    Assumptions:
        For 3-D inputs the leading dimension is time; for 4-D inputs the first
        two dimensions are time and depth.
    """
    final_vort = np.zeros(u.shape)
    # ------- 2D ----------
    if len(u.shape) == 2:
        if dist_grid is None:
            vort = np.diff(v, axis=1)[:-1, :] - np.diff(u, axis=0)[:, :-1]
        else:
            vort = np.diff(v, axis=1)[:-1, :] / dist_grid[0] - np.diff(u, axis=0)[:, :-1] / dist_grid[1]
        vort_dims = vort.shape
        final_vort[:vort_dims[0], :vort_dims[1]] = vort

    # ------- 3D ----------
    if len(u.shape) == 3:  # Assumes first dimension is time
        if dist_grid is None:
            vort = np.diff(v, axis=2)[:, : -1, :] - np.diff(u, axis=1)[:, :, :-1]
        else:
            vort = np.diff(v, axis=2)[:, : -1, :] / dist_grid[0] - np.diff(u, axis=1)[:, :, :-1] / dist_grid[1]

        vort_dims = vort.shape
        final_vort[:, :vort_dims[1], :vort_dims[2]] = vort

    # ------- 4D ----------
    if len(u.shape) == 4:  # Assumes first two dimension are time and depth
        if dist_grid is None:
            vort = np.diff(v, axis=3)[:, :, : -1, :] - np.diff(u, axis=2)[:, :, :, :-1]
        else:
            vort = np.diff(v, axis=3)[:, :, : -1, :] / dist_grid[0] - np.diff(u, axis=2)[:, :, :, :-1] / dist_grid[1]

        vort_dims = vort.shape
        final_vort[:, :, :vort_dims[2], :vort_dims[3]] = vort

    return final_vort
