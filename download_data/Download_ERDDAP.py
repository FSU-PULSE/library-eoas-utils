"""HTTP download helpers for public NOAA ERDDAP gridded products."""

import os
import sys
import requests
import datetime
import xarray as xr
from io_utils.io_common import create_folder

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_remote_content_length(url: str) -> int | None:
    """Return the remote ``Content-Length`` header when available.

    Args:
        url: HTTP(S) URL to probe with a HEAD request.

    Returns:
        File size in bytes, or ``None`` when unknown or the request fails.
    """
    try:
        response = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=20)
        if response.status_code == 200 and response.headers.get("content-length"):
            return int(response.headers["content-length"])
    except Exception:
        return None
    return None


def skip_existing_file(dest_path: str, label: str, remote_size: int | None = None) -> bool | None:
    """Decide whether a local file can be skipped as already complete.

    Args:
        dest_path: Local file path.
        label: Human-readable label used only for logging elsewhere.
        remote_size: Optional remote byte size for equality check.

    Returns:
        ``True`` when the existing file should be skipped, ``None`` when a
        download should proceed.
    """
    if not os.path.exists(dest_path):
        return None

    local_size = os.path.getsize(dest_path)
    if local_size <= 0:
        return None

    if remote_size is not None and local_size != remote_size:
        return None

    return True


def download_via_http(url: str, dest_path: str, label: str) -> tuple[bool, str]:
    """Download a URL to disk, skipping when a matching file already exists.

    Args:
        url: Remote file URL.
        dest_path: Local destination path.
        label: Short description for status messages.

    Returns:
        Tuple ``(success, message)``.

    Raises:
        Exception: When the HTTP status is not 200 or the transfer fails.
    """
    try:
        remote_size = get_remote_content_length(url)
        if skip_existing_file(dest_path, label, remote_size=remote_size):
            print(f"{label} already exists with matching size. Skipping.")
            return True, f"{label} already exists."

        response = requests.get(url, headers=HEADERS, timeout=60)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True, f"Successfully downloaded {label} to: {os.path.basename(dest_path)}"
        else:
            raise Exception(f"HTTP Status {response.status_code}: {response.reason}")
    except Exception as e:
        raise Exception(f"HTTP download failed for {label}: {e}")


def download_by_day(date_val, dtype, bbox, dest_dir, dest_file):
    """Download a public ERDDAP subset for a single day.

    Args:
        date_val: Target date (``datetime.date``-like).
        dtype: Product key, e.g. ``"erddap_sst"`` or ``"erddap_ssh"``.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        dest_dir: Output directory (created if missing).
        dest_file: Output NetCDF file name.

    Side effects:
        For SSH products, writes a temporary file, renames ``sla`` to ``adt``,
        and remaps longitudes from ``0..360`` to ``-180..180``.
    """
    create_folder(dest_dir)
    dest_path = os.path.join(dest_dir, dest_file)
    date_str = date_val.strftime("%Y-%m-%d")

    if dtype == "erddap_sst":
        url = (
            f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.nc"
            f"?analysed_sst%5B({date_str}T09:00:00Z):1:({date_str}T09:00:00Z)%5D"
            f"%5B({bbox[1]}):1:({bbox[3]})%5D%5B({bbox[0]}):1:({bbox[2]})%5D"
        )
        download_via_http(url, dest_path, "Public MUR SST")

    elif dtype == "erddap_ssh":
        lon_c = [
            bbox[0] + 360 if bbox[0] < 0 else bbox[0],
            bbox[2] + 360 if bbox[2] < 0 else bbox[2],
        ]
        url = (
            f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/nesdisSSH1day_Lon0360.nc"
            f"?sla%5B({date_str}T12:00:00Z):1:({date_str}T12:00:00Z)%5D"
            f"%5B({bbox[1]}):1:({bbox[3]})%5D%5B({lon_c[0]}):1:({lon_c[1]})%5D"
        )

        temp_file = dest_path + ".temp"
        try:
            download_via_http(url, temp_file, "Public SSH")
            ds = xr.open_dataset(temp_file)
            rename_dict = {}
            if 'lon' in ds.coords and 'longitude' not in ds.coords:
                rename_dict['lon'] = 'longitude'
            if 'lat' in ds.coords and 'latitude' not in ds.coords:
                rename_dict['lat'] = 'latitude'
            if rename_dict:
                ds = ds.rename(rename_dict)

            if 'longitude' in ds.coords:
                ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180)
                ds = ds.sortby('longitude')

            if 'sla' in ds.variables:
                ds = ds.rename({'sla': 'adt'})

            ds.to_netcdf(dest_path)
            ds.close()
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

    else:
        raise ValueError(f"Unsupported ERDDAP dtype: {dtype}")
