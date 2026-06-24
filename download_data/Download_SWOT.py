"""Download and merge SWOT KaRIn L2 SSH swath points for the dashboard."""

from __future__ import annotations

import datetime
import os
import shutil
import tempfile
from os.path import join

import earthaccess
import numpy as np
import xarray as xr

from io_utils.io_common import create_folder

SWOT_SHORT_NAME = "SWOT_L2_LR_SSH_2.0"
DEFAULT_MAX_POINTS = 300_000


def _bbox_to_cmr(bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Convert dashboard bbox to CMR ``(west, south, east, north)`` order.

    Args:
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.

    Returns:
        Bounding box in CMR order.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    return lon_min, lat_min, lon_max, lat_max


def _default_daily_filename(date_val: datetime.date) -> str:
    """Return the dashboard filename for a SWOT daily merge file.

    Args:
        date_val: Target calendar date.

    Returns:
        NetCDF filename such as ``SWOT_KARIN_L2_SSH_2024-02-01.nc``.
    """
    return f"SWOT_KARIN_L2_SSH_{date_val.year}-{date_val.month:02d}-{date_val.day:02d}.nc"


def _extract_swath_points(
    ds: xr.Dataset,
    bbox: tuple[float, float, float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract finite KaRIn SSH points inside a bounding box.

    Args:
        ds: Open SWOT L2 LR SSH granule dataset.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.

    Returns:
        Tuple of ``(lon, lat, ssh)`` one-dimensional arrays.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    lat = ds["latitude"].values.astype(np.float64).ravel()
    lon = ds["longitude"].values.astype(np.float64).ravel()
    ssh = ds["ssh_karin"].values.astype(np.float64).ravel()

    if np.nanmax(lon) > 180.0:
        lon = ((lon + 180.0) % 360.0) - 180.0

    mask = (
        (lon >= lon_min)
        & (lon <= lon_max)
        & (lat >= lat_min)
        & (lat <= lat_max)
        & np.isfinite(ssh)
        & (np.abs(ssh) < 5.0)
    )
    if "ssh_karin_qual" in ds:
        qual = ds["ssh_karin_qual"].values.ravel()
        mask = mask & np.isfinite(qual) & (qual <= 1.0)

    return lon[mask], lat[mask], ssh[mask]


def _subsample_points(
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    ssh_pts: np.ndarray,
    max_points: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Uniformly subsample point arrays to a maximum length.

    Args:
        lon_pts: Longitude values.
        lat_pts: Latitude values.
        ssh_pts: SSH values.
        max_points: Maximum number of points to keep.

    Returns:
        Subsampled ``(lon, lat, ssh)`` arrays.
    """
    if len(ssh_pts) <= max_points:
        return lon_pts, lat_pts, ssh_pts
    stride = int(np.ceil(len(ssh_pts) / max_points))
    return lon_pts[::stride], lat_pts[::stride], ssh_pts[::stride]


def _save_point_dataset(
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    ssh_pts: np.ndarray,
    dest_path: str,
) -> None:
    """Write merged SWOT swath points to a dashboard-friendly NetCDF file.

    Args:
        lon_pts: Longitude values.
        lat_pts: Latitude values.
        ssh_pts: KaRIn SSH values in metres.
        dest_path: Output NetCDF path.
    """
    out_ds = xr.Dataset(
        data_vars={
            "ssh_karin": (("n_points",), ssh_pts.astype(np.float32)),
        },
        coords={
            "lon": (("n_points",), lon_pts.astype(np.float64)),
            "lat": (("n_points",), lat_pts.astype(np.float64)),
        },
    )
    out_ds["ssh_karin"].attrs["units"] = "m"
    out_ds.to_netcdf(dest_path)
    out_ds.close()


def download_by_day(
    date_val: datetime.date,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
    max_points: int = DEFAULT_MAX_POINTS,
) -> bool:
    """Download and merge SWOT KaRIn L2 SSH swaths for one day.

    Args:
        date_val: Target calendar date.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the merged NetCDF output.
        output_filename: Optional local filename override.
        max_points: Maximum merged points written to disk.

    Returns:
        True when the output file exists and is non-empty.

    Raises:
        RuntimeError: When no SWOT granules intersect the date and bbox.
    """
    create_folder(output_folder)
    dest_path = join(output_folder, output_filename or _default_daily_filename(date_val))
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True

    earthaccess.login(strategy="netrc")
    start_time = f"{date_val.strftime('%Y-%m-%d')}T00:00:00Z"
    end_time = f"{date_val.strftime('%Y-%m-%d')}T23:59:59Z"
    results = earthaccess.search_data(
        short_name=SWOT_SHORT_NAME,
        bounding_box=_bbox_to_cmr(bbox),
        temporal=(start_time, end_time),
        granule_name="*Expert*",
    )
    if not results:
        raise RuntimeError(
            f"No SWOT KaRIn L2 Expert granules found for {date_val} in bbox {bbox}"
        )

    lon_parts: list[np.ndarray] = []
    lat_parts: list[np.ndarray] = []
    ssh_parts: list[np.ndarray] = []
    temp_dir = tempfile.mkdtemp(prefix="swot_karin_l2_")

    try:
        downloaded = earthaccess.download(results, local_path=temp_dir)
        for file_path in downloaded:
            ds = xr.open_dataset(file_path)
            lon_pts, lat_pts, ssh_pts = _extract_swath_points(ds, bbox)
            ds.close()
            if len(ssh_pts) > 0:
                lon_parts.append(lon_pts)
                lat_parts.append(lat_pts)
                ssh_parts.append(ssh_pts)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if not ssh_parts:
        raise RuntimeError(
            f"No finite SWOT KaRIn SSH points found for {date_val} in bbox {bbox}"
        )

    lon_all = np.concatenate(lon_parts)
    lat_all = np.concatenate(lat_parts)
    ssh_all = np.concatenate(ssh_parts)
    lon_all, lat_all, ssh_all = _subsample_points(lon_all, lat_all, ssh_all, max_points)
    _save_point_dataset(lon_all, lat_all, ssh_all, dest_path)
    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0


def download_for_dashboard(
    date_val: datetime.date,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str,
) -> bool:
    """Download the merged SWOT KaRIn L2 file expected by the dashboard.

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
    )
