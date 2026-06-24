"""Efficient local file loading for the satellite dashboard."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from download_data.dashboard_cache import (
    clear_slice_cache,
    get_cached_slice,
    make_slice_cache_key,
    set_cached_slice,
)
from download_data.dashboard_products import SATELLITE_PRODUCTS

MAX_GRID_AXIS_POINTS = 250


def invalidate_slice_cache() -> None:
    """Clear cached dashboard slices after downloads or deletes."""
    clear_slice_cache()


def _cap_grid(
    lons: np.ndarray,
    lats: np.ndarray,
    values: np.ndarray,
    max_points: int = MAX_GRID_AXIS_POINTS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Downsample a 2-D grid so each axis stays within ``max_points``.

    Args:
        lons: Longitude coordinates.
        lats: Latitude coordinates.
        values: Data array with at least two dimensions.
        max_points: Maximum points allowed per axis.

    Returns:
        Downsampled ``(lons, lats, values)`` arrays.
    """
    if values.ndim < 2:
        return lons, lats, values

    stride_lon = max(1, int(np.ceil(lons.shape[0] / max_points)))
    stride_lat = max(1, int(np.ceil(lats.shape[0] / max_points)))
    if stride_lon == 1 and stride_lat == 1:
        return lons, lats, values

    lons = lons[::stride_lon]
    lats = lats[::stride_lat]
    values = values[::stride_lat, ::stride_lon]
    return lons, lats, values


def standardize_coords(ds: xr.Dataset, lon_var: str = "longitude", lat_var: str = "latitude") -> xr.Dataset:
    """Rename and normalize longitude coordinates to ``[-180, 180]``.

    Args:
        ds: Input dataset.
        lon_var: Target longitude coordinate name.
        lat_var: Target latitude coordinate name.

    Returns:
        Dataset with standardized coordinate names and longitudes.
    """
    rename_dict: dict[str, str] = {}
    for coord in ds.coords:
        if coord.lower() in {"lon", "longitude", "lons"} and coord != lon_var:
            rename_dict[coord] = lon_var
        if coord.lower() in {"lat", "latitude", "lats"} and coord != lat_var:
            rename_dict[coord] = lat_var
    if rename_dict:
        ds = ds.rename(rename_dict)

    lons = ds[lon_var].values
    if np.max(lons) > 180:
        ds = ds.assign_coords({lon_var: ((ds[lon_var] + 180) % 360) - 180})
        ds = ds.sortby(lon_var)
    return ds


def load_dataset_slice(
    sensor_type: str,
    product_id: str,
    date_val,
    root_dir: str,
    bbox: tuple[float, float, float, float],
    stride: int = 1,
    compute_loop_current: bool = False,
    use_cache: bool = True,
) -> tuple[Any | None, str | None]:
    """Load and subset one local product for dashboard visualization.

    Args:
        sensor_type: Dashboard variable tab id.
        product_id: Product key within the tab.
        date_val: Target date for the product file name.
        root_dir: Local satellite data root directory.
        bbox: Bounding box as ``(lon_min, lon_max, lat_min, lat_max)``.
        stride: Visualization subsample stride.
        compute_loop_current: Whether to compute SSH loop-current contours.
        use_cache: Whether to read/write the in-memory slice cache.

    Returns:
        Tuple of ``(data, error)`` where ``data`` is a plotting payload or ``None``.
    """
    prod_info = SATELLITE_PRODUCTS[sensor_type][product_id]
    file_name = prod_info["file_fmt"](date_val)
    file_path = os.path.join(root_dir, prod_info["dir_rel"], file_name)

    if not os.path.exists(file_path):
        return None, "Local file not found"

    cache_key = make_slice_cache_key(
        sensor_type,
        product_id,
        file_path,
        bbox,
        stride,
        compute_loop_current,
    )
    if use_cache:
        cached = get_cached_slice(cache_key)
        if cached is not None:
            return cached

    try:
        payload = _load_dataset_slice_uncached(
            sensor_type,
            prod_info,
            file_path,
            bbox,
            stride,
            compute_loop_current,
        )
    except Exception as exc:
        payload = (None, f"Error reading NetCDF file: {exc}")

    if use_cache:
        set_cached_slice(cache_key, payload)
    return payload


def _load_dataset_slice_uncached(
    sensor_type: str,
    prod_info: dict[str, Any],
    file_path: str,
    bbox: tuple[float, float, float, float],
    stride: int,
    compute_loop_current: bool,
) -> tuple[Any | None, str | None]:
    """Load one product slice without touching the cache."""
    if file_path.lower().endswith(".csv"):
        return _load_csv_slice(sensor_type, prod_info, file_path, bbox, stride)

    with xr.open_dataset(file_path, decode_times=False) as ds:
        lon_var, lat_var = prod_info["coords"]
        ds = standardize_coords(ds, lon_var, lat_var)

        if prod_info.get("swath_points"):
            return _load_swath_slice(sensor_type, prod_info, ds, lon_var, lat_var, bbox, stride)

        lat_vals = ds[lat_var].values
        if lat_vals[0] > lat_vals[-1]:
            ds_subset = ds.sel({lat_var: slice(bbox[3], bbox[2]), lon_var: slice(bbox[0], bbox[1])})
        else:
            ds_subset = ds.sel({lat_var: slice(bbox[2], bbox[3]), lon_var: slice(bbox[0], bbox[1])})

        var_name = prod_info["var_name"]
        if var_name not in ds_subset.variables:
            visualizable_vars = [name for name in ds_subset.variables if len(ds_subset[name].shape) >= 2]
            if not visualizable_vars:
                return None, f"Variable '{var_name}' not found in NetCDF file"
            var_name = visualizable_vars[0]

        data_var = ds_subset[var_name]
        while len(data_var.shape) > 2:
            data_var = data_var.isel({data_var.dims[0]: 0})

        lon_slice = slice(None, None, stride) if stride > 1 else slice(None)
        lat_slice = slice(None, None, stride) if stride > 1 else slice(None)
        if stride > 1:
            data_var = data_var.isel({lon_var: lon_slice, lat_var: lat_slice})

        values = data_var.load().values
        lons = ds_subset[lon_var].isel({lon_var: lon_slice}).values
        lats = ds_subset[lat_var].isel({lat_var: lat_slice}).values

    if sensor_type == "sst" and np.nanmax(values) > 200:
        values = values - 273.15

    unit_label = prod_info["unit"]
    if sensor_type == "chlora":
        values = np.where(values > 0, np.log10(values), np.nan)
        unit_label = "log10(Chlorophyll-A) (mg/m³)"

    if values.ndim >= 2:
        lons, lats, values = _cap_grid(lons, lats, values)

    lc_coords = None
    if compute_loop_current and sensor_type == "ssh" and var_name == "adt":
        try:
            from proc_utils.gom import lc_from_ssh

            lc = lc_from_ssh(values, lons, lats)
            if lc is not None:
                lc_coords = list(lc)
        except Exception as exc:
            print(f"Error extracting Loop Current: {exc}")

    if sensor_type == "ssh":
        return (lons, lats, values, prod_info["colorscale"], unit_label, lc_coords), None
    return (lons, lats, values, prod_info["colorscale"], unit_label), None


def _load_csv_slice(
    sensor_type: str,
    prod_info: dict[str, Any],
    file_path: str,
    bbox: tuple[float, float, float, float],
    stride: int,
) -> tuple[Any | None, str | None]:
    """Load an along-track CSV product."""
    df = pd.read_csv(file_path)
    lon_var, lat_var = prod_info["coords"]
    var_name = prod_info["var_name"]

    if "variable" in df.columns and "value" in df.columns:
        df = df[df["variable"] == var_name].copy()
        value_col = "value"
    elif var_name in df.columns:
        value_col = var_name
    else:
        return None, f"Variable '{var_name}' not found in CSV file"

    if lon_var not in df.columns or lat_var not in df.columns:
        return None, f"Coordinates '{lon_var}'/'{lat_var}' not found in CSV file"
    if df.empty:
        return None, "No along-track points found for the selected region/date"

    lons = df[lon_var].to_numpy(dtype=float)
    lats = df[lat_var].to_numpy(dtype=float)
    values = df[value_col].to_numpy(dtype=float)

    if np.nanmax(lons) > 180:
        lons = ((lons + 180) % 360) - 180

    mask = (
        (lons >= bbox[0]) & (lons <= bbox[1]) &
        (lats >= bbox[2]) & (lats <= bbox[3]) &
        np.isfinite(values)
    )
    lons = lons[mask]
    lats = lats[mask]
    values = values[mask]
    if len(values) == 0:
        return None, "No finite along-track points found for the selected region/date"
    if stride > 1:
        lons = lons[::stride]
        lats = lats[::stride]
        values = values[::stride]

    unit_label = prod_info["unit"]
    if sensor_type == "ssh":
        return (lons, lats, values, prod_info["colorscale"], unit_label, None), None
    return (lons, lats, values, prod_info["colorscale"], unit_label), None


def _load_swath_slice(
    sensor_type: str,
    prod_info: dict[str, Any],
    ds: xr.Dataset,
    lon_var: str,
    lat_var: str,
    bbox: tuple[float, float, float, float],
    stride: int,
) -> tuple[Any | None, str | None]:
    """Load a swath-style NetCDF product."""
    var_name = prod_info["var_name"]
    if var_name not in ds.variables:
        return None, f"Variable '{var_name}' not found in NetCDF file"

    lons = ds[lon_var].values.astype(float).ravel()
    lats = ds[lat_var].values.astype(float).ravel()
    values = ds[var_name].values.astype(float).ravel()

    if np.nanmax(lons) > 180:
        lons = ((lons + 180) % 360) - 180

    mask = (
        (lons >= bbox[0]) & (lons <= bbox[1]) &
        (lats >= bbox[2]) & (lats <= bbox[3]) &
        np.isfinite(values)
    )
    lons = lons[mask]
    lats = lats[mask]
    values = values[mask]
    if len(values) == 0:
        return None, "No finite swath points found for the selected region/date"
    if stride > 1:
        lons = lons[::stride]
        lats = lats[::stride]
        values = values[::stride]

    unit_label = prod_info["unit"]
    if sensor_type == "sst" and np.nanmax(values) > 200:
        values = values - 273.15

    if sensor_type == "ssh":
        return (lons, lats, values, prod_info["colorscale"], unit_label, None), None
    return (lons, lats, values, prod_info["colorscale"], unit_label), None
