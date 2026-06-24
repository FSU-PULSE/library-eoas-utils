"""In-memory cache for dashboard NetCDF slices."""

from __future__ import annotations

import os
from typing import Any

_MAX_CACHE_ENTRIES = 128
_slice_cache: dict[tuple[Any, ...], tuple[Any, ...]] = {}


def make_slice_cache_key(
    sensor_type: str,
    product_id: str,
    file_path: str,
    bbox: tuple[float, float, float, float],
    stride: int,
    compute_loop_current: bool,
) -> tuple[Any, ...]:
    """Build a cache key for one sliced dataset.

    Args:
        sensor_type: Dashboard variable tab id.
        product_id: Product key within the tab.
        file_path: Absolute or relative NetCDF path.
        bbox: Bounding box as ``(lon_min, lon_max, lat_min, lat_max)``.
        stride: Visualization subsample stride.
        compute_loop_current: Whether loop-current contours were requested.

    Returns:
        Hashable cache key including file modification time.
    """
    mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
    rounded_bbox = tuple(round(float(value), 4) for value in bbox)
    return (
        sensor_type,
        product_id,
        file_path,
        mtime,
        rounded_bbox,
        int(stride),
        bool(compute_loop_current),
    )


def get_cached_slice(cache_key: tuple[Any, ...]) -> tuple[Any, ...] | None:
    """Return a cached slice payload when present.

    Args:
        cache_key: Key produced by :func:`make_slice_cache_key`.

    Returns:
        Cached ``(data, err)`` tuple or ``None``.
    """
    return _slice_cache.get(cache_key)


def set_cached_slice(cache_key: tuple[Any, ...], payload: tuple[Any, ...]) -> None:
    """Store a slice payload in the in-memory cache.

    Args:
        cache_key: Key produced by :func:`make_slice_cache_key`.
        payload: ``(data, err)`` tuple returned by the loader.
    """
    if cache_key in _slice_cache:
        _slice_cache[cache_key] = payload
        return

    if len(_slice_cache) >= _MAX_CACHE_ENTRIES:
        oldest_key = next(iter(_slice_cache))
        _slice_cache.pop(oldest_key, None)
    _slice_cache[cache_key] = payload


def clear_slice_cache() -> None:
    """Remove all cached slice payloads."""
    _slice_cache.clear()
