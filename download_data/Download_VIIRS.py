"""Download NOAA STAR VIIRS ACSPO L2P sea-surface temperature swath data from PO.DAAC."""

from __future__ import annotations

import datetime
import os
import shutil
import tempfile
from calendar import monthrange
from os.path import join

import earthaccess
import numpy as np
import xarray as xr

from io_utils.io_common import create_folder, dotdict

DEFAULT_OUTPUT_FOLDER = "./test_data/Satellite_Data_Examples/SST/VIIRS_ACSPO_L2P"
DEFAULT_MAX_POINTS = 250_000
DEFAULT_MIN_QUALITY = 5

VIIRS_L2P_PRODUCTS: dict[str, dotdict] = {
    "npp": dotdict({
        "label": "Suomi-NPP VIIRS ACSPO L2P SST",
        "short_name": "VIIRS_NPP-STAR-L2P-v2.80",
        "platform": "SNPP",
    }),
    "n20": dotdict({
        "label": "NOAA-20 VIIRS ACSPO L2P SST",
        "short_name": "VIIRS_N20-STAR-L2P-v2.80",
        "platform": "NOAA-20",
    }),
    "n21": dotdict({
        "label": "NOAA-21 VIIRS ACSPO L2P SST",
        "short_name": "N21-VIIRS-L2P-ACSPO-v2.80",
        "platform": "NOAA-21",
    }),
}

VIIRS_JPSS_L2P = dotdict({
    "label": "JPSS VIIRS ACSPO L2P SST (SNPP + NOAA-20 + NOAA-21)",
    "satellite_keys": ("npp", "n20", "n21"),
    "var_name": "sea_surface_temperature",
    "lon_var": "lon",
    "lat_var": "lat",
})


def _resolve_satellite_keys(satellite_keys: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    """Return validated VIIRS satellite keys.

    Args:
        satellite_keys: Optional subset of keys in :data:`VIIRS_L2P_PRODUCTS`.

    Returns:
        Tuple of satellite keys to include in a download.
    """
    if satellite_keys is None:
        return tuple(VIIRS_L2P_PRODUCTS.keys())
    for key in satellite_keys:
        if key not in VIIRS_L2P_PRODUCTS:
            raise KeyError(f"Unknown VIIRS satellite key: {key}")
    return tuple(satellite_keys)


def _bbox_to_cmr(bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Convert dashboard bbox to CMR ``(west, south, east, north)`` order.

    Args:
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.

    Returns:
        Bounding box in CMR order.
    """
    return (bbox[0], bbox[1], bbox[2], bbox[3])


def _default_daily_filename(date_val: datetime.date) -> str:
    """Build the default merged VIIRS L2P filename for one day.

    Args:
        date_val: Target calendar date.

    Returns:
        NetCDF filename such as ``VIIRS_ACSPO_L2P_SST_2026-05-05.nc``.
    """
    return f"VIIRS_ACSPO_L2P_SST_{date_val.year}-{date_val.month:02d}-{date_val.day:02d}.nc"


def _extract_swath_points(
    ds: xr.Dataset,
    bbox: tuple[float, float, float, float],
    min_quality: int = DEFAULT_MIN_QUALITY,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract finite VIIRS L2P SST points inside a bounding box.

    Args:
        ds: Open VIIRS L2P granule dataset.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        min_quality: Minimum ``quality_level`` to retain when available.

    Returns:
        Tuple of ``(lon, lat, sst)`` one-dimensional arrays.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    sst = ds["sea_surface_temperature"]
    if "time" in sst.dims:
        sst = sst.isel(time=0)

    lon = ds["lon"]
    lat = ds["lat"]
    mask = (
        (lon >= lon_min)
        & (lon <= lon_max)
        & (lat >= lat_min)
        & (lat <= lat_max)
        & np.isfinite(sst)
    )
    if "quality_level" in ds:
        quality = ds["quality_level"]
        if "time" in quality.dims:
            quality = quality.isel(time=0)
        mask = mask & (quality >= min_quality)

    lon_pts = lon.values[mask.values].astype(np.float64)
    lat_pts = lat.values[mask.values].astype(np.float64)
    sst_pts = sst.values[mask.values].astype(np.float32)
    return lon_pts, lat_pts, sst_pts


def _subsample_points(
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    sst_pts: np.ndarray,
    max_points: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Uniformly subsample point arrays to a maximum length.

    Args:
        lon_pts: Longitude values.
        lat_pts: Latitude values.
        sst_pts: SST values.
        max_points: Maximum number of points to keep.

    Returns:
        Subsampled ``(lon, lat, sst)`` arrays.
    """
    if len(sst_pts) <= max_points:
        return lon_pts, lat_pts, sst_pts
    stride = int(np.ceil(len(sst_pts) / max_points))
    return lon_pts[::stride], lat_pts[::stride], sst_pts[::stride]


def _save_point_dataset(
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    sst_pts: np.ndarray,
    dest_path: str,
) -> None:
    """Write merged VIIRS swath points to a dashboard-friendly NetCDF file.

    Args:
        lon_pts: Longitude values.
        lat_pts: Latitude values.
        sst_pts: SST values in Kelvin.
        dest_path: Output NetCDF path.
    """
    out_ds = xr.Dataset(
        data_vars={
            "sea_surface_temperature": (("n_points",), sst_pts),
        },
        coords={
            "lon": (("n_points",), lon_pts),
            "lat": (("n_points",), lat_pts),
        },
    )
    out_ds["sea_surface_temperature"].attrs["units"] = "kelvin"
    out_ds.to_netcdf(dest_path)
    out_ds.close()


def _download_satellite_day_points(
    date_val: datetime.date,
    satellite_key: str,
    bbox: tuple[float, float, float, float],
    min_quality: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Download and merge all VIIRS L2P granules for one satellite and day.

    Args:
        date_val: Target calendar date.
        satellite_key: Key in :data:`VIIRS_L2P_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        min_quality: Minimum ``quality_level`` to retain.

    Returns:
        Concatenated ``(lon, lat, sst)`` arrays for the day.
    """
    config = VIIRS_L2P_PRODUCTS[satellite_key]
    start_time = f"{date_val.strftime('%Y-%m-%d')}T00:00:00Z"
    end_time = f"{date_val.strftime('%Y-%m-%d')}T23:59:59Z"

    results = earthaccess.search_data(
        short_name=config.short_name,
        bounding_box=_bbox_to_cmr(bbox),
        temporal=(start_time, end_time),
    )
    if not results:
        return np.array([]), np.array([]), np.array([])

    lon_parts: list[np.ndarray] = []
    lat_parts: list[np.ndarray] = []
    sst_parts: list[np.ndarray] = []
    temp_dir = tempfile.mkdtemp(prefix="viirs_l2p_")

    try:
        downloaded = earthaccess.download(results, local_path=temp_dir)
        for file_path in downloaded:
            ds = xr.open_dataset(file_path)
            lon_pts, lat_pts, sst_pts = _extract_swath_points(ds, bbox, min_quality=min_quality)
            ds.close()
            if len(sst_pts) > 0:
                lon_parts.append(lon_pts)
                lat_parts.append(lat_pts)
                sst_parts.append(sst_pts)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if not sst_parts:
        return np.array([]), np.array([]), np.array([])

    return (
        np.concatenate(lon_parts),
        np.concatenate(lat_parts),
        np.concatenate(sst_parts),
    )


def download_by_day(
    date_val: datetime.date,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
    satellite_keys: tuple[str, ...] | list[str] | None = None,
    min_quality: int = DEFAULT_MIN_QUALITY,
    max_points: int = DEFAULT_MAX_POINTS,
) -> bool:
    """Download and merge JPSS VIIRS ACSPO L2P SST swaths for one day.

    Args:
        date_val: Target calendar date.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the merged NetCDF output.
        output_filename: Optional local filename override.
        satellite_keys: Optional subset of ``npp``, ``n20``, and ``n21``.
        min_quality: Minimum VIIRS ``quality_level`` to retain.
        max_points: Maximum merged points written to disk.

    Returns:
        True when the output file exists and is non-empty.
    """
    create_folder(output_folder)
    dest_path = join(output_folder, output_filename or _default_daily_filename(date_val))
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True

    earthaccess.login(strategy="netrc")
    keys = _resolve_satellite_keys(satellite_keys)

    lon_parts: list[np.ndarray] = []
    lat_parts: list[np.ndarray] = []
    sst_parts: list[np.ndarray] = []
    for satellite_key in keys:
        lon_pts, lat_pts, sst_pts = _download_satellite_day_points(
            date_val,
            satellite_key,
            bbox,
            min_quality,
        )
        if len(sst_pts) > 0:
            lon_parts.append(lon_pts)
            lat_parts.append(lat_pts)
            sst_parts.append(sst_pts)

    if not sst_parts:
        raise RuntimeError(f"No VIIRS ACSPO L2P granules found for {date_val} in bbox {bbox}")

    lon_all = np.concatenate(lon_parts)
    lat_all = np.concatenate(lat_parts)
    sst_all = np.concatenate(sst_parts)
    lon_all, lat_all, sst_all = _subsample_points(lon_all, lat_all, sst_all, max_points)
    _save_point_dataset(lon_all, lat_all, sst_all, dest_path)
    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0


def download_by_month(
    year: int,
    month: int,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    satellite_keys: tuple[str, ...] | list[str] | None = None,
) -> bool:
    """Download merged VIIRS ACSPO L2P SST for each day in a month.

    Args:
        year: Calendar year.
        month: Calendar month ``1..12``.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Base output directory.
        satellite_keys: Optional subset of VIIRS platforms.

    Returns:
        True when every day in the month downloaded successfully.
    """
    month_folder = join(output_folder, f"{year}-{month:02d}")
    success = True
    last_day = monthrange(year, month)[1]
    for day in range(1, last_day + 1):
        date_val = datetime.date(year, month, day)
        result = download_by_day(date_val, bbox, month_folder, satellite_keys=satellite_keys)
        success = success and result
    return success


def download_by_year(
    year: int,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    satellite_keys: tuple[str, ...] | list[str] | None = None,
) -> bool:
    """Download merged VIIRS ACSPO L2P SST for each month in a year.

    Args:
        year: Calendar year.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Base output directory.
        satellite_keys: Optional subset of VIIRS platforms.

    Returns:
        True when every month downloaded successfully.
    """
    success = True
    for month in range(1, 13):
        result = download_by_month(year, month, bbox, output_folder, satellite_keys=satellite_keys)
        success = success and result
    return success


def download_for_dashboard(
    date_val: datetime.date,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str,
) -> bool:
    """Download the merged JPSS VIIRS L2P file expected by the dashboard.

    Args:
        date_val: Target calendar date.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the output NetCDF file.
        output_filename: Dashboard filename from product metadata.

    Returns:
        True when the dashboard file exists locally.
    """
    return download_by_day(
        date_val,
        bbox,
        output_folder,
        output_filename=output_filename,
        satellite_keys=VIIRS_JPSS_L2P.satellite_keys,
    )


if __name__ == "__main__":
    bbox_gom = (-98.0, 7.5, -60.0, 50.0)
    download_by_day(datetime.date(2026, 5, 5), bbox_gom, DEFAULT_OUTPUT_FOLDER)
