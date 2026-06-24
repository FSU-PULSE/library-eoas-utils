"""Download RSS REMSS and NOAA CoastWatch SMAP sea-surface salinity products."""

# %%
import os
from os.path import join

import requests
import xarray as xr

from io_utils.io_common import create_folder

## This program downloads SSS data from REMSS and NOAA CoastWatch STAR.

COASTWATCH_SMAP_DAILY_BASE_URL = (
    "https://www.star.nesdis.noaa.gov/data/socd1/coastwatch/products/smap/nc"
)
COASTWATCH_SMAP_DAILY_VAR = "sss"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}


def _download_remss_file(url: str, output_file: str) -> bool:
    """
    Download a single REMSS NetCDF file to the target path.

    Parameters
    ----------
    url : str
        Remote REMSS file URL.
    output_file : str
        Local destination path.

    Returns
    -------
    bool
        True when the file was downloaded successfully.
    """
    try:
        print(f"Downloading: {url}")
        response = requests.get(url, timeout=120)
        if response.status_code == 200:
            with open(output_file, "wb") as handle:
                handle.write(response.content)
            return True
        print(f"Failed to download {url}: HTTP status {response.status_code}")
        return False
    except Exception as exc:
        print(f"Failed to download {url}: {exc}")
        return False


def _coastwatch_daily_remote_name(year: int, day_of_year: int) -> str:
    """Build the CoastWatch STAR filename for one SMAP daily-mean file.

    Args:
        year: Calendar year.
        day_of_year: Day of year ``1..366``.

    Returns:
        Remote NetCDF filename such as ``SP_D2026125_Map_SATSSS_data_1day.nc``.
    """
    return f"SP_D{year}{day_of_year:03d}_Map_SATSSS_data_1day.nc"


def _subset_sss_dataset(
    ds: xr.Dataset,
    bbox: tuple[float, float, float, float] | None,
    var_name: str = COASTWATCH_SMAP_DAILY_VAR,
) -> xr.Dataset:
    """Spatially subset a CoastWatch SMAP SSS dataset.

    Args:
        ds: Input dataset with ``lon``/``lat`` coordinates.
        bbox: Optional ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        var_name: Salinity variable to retain.

    Returns:
        Subset dataset ready for export.
    """
    if bbox is None:
        subset = ds
    else:
        lon_min, lat_min, lon_max, lat_max = bbox
        lat_values = ds["lat"].values
        if len(lat_values) > 1 and lat_values[0] > lat_values[-1]:
            lat_slice = slice(lat_max, lat_min)
        else:
            lat_slice = slice(lat_min, lat_max)
        subset = ds.sel(lon=slice(lon_min, lon_max), lat=lat_slice)

    if "altitude" in subset.dims and subset.sizes.get("altitude", 0) == 1:
        subset = subset.squeeze("altitude", drop=True)

    keep_vars = [var_name]
    for coord_name in ("lon", "lat", "time"):
        if coord_name in subset.coords:
            keep_vars.append(coord_name)
    return subset[keep_vars]


def download_coastwatch_daily_single_day(
    year: int,
    day_of_year: int,
    output_folder: str,
    bbox: tuple[float, float, float, float] | None = None,
    output_filename: str | None = None,
) -> bool:
    """Download one NOAA CoastWatch SMAP NRT L3 daily-mean SSS file.

    Args:
        year: Calendar year.
        day_of_year: Day of year ``1..366``.
        output_folder: Directory where the NetCDF file should be saved.
        bbox: Optional ``(lon_min, lat_min, lon_max, lat_max)`` subset in degrees.
        output_filename: Optional local filename expected by the dashboard.

    Returns:
        True when the file exists locally after the download attempt.
    """
    create_folder(output_folder)
    remote_name = _coastwatch_daily_remote_name(year, day_of_year)
    if output_filename is None:
        output_filename = remote_name

    output_file = join(output_folder, output_filename)
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return True

    url = f"{COASTWATCH_SMAP_DAILY_BASE_URL}/{remote_name}"
    temp_path = join(output_folder, f".tmp_{remote_name}")
    try:
        if not _download_remss_file(url, temp_path):
            return False

        ds = xr.open_dataset(temp_path)
        subset = _subset_sss_dataset(ds, bbox)
        subset.to_netcdf(output_file)
        ds.close()
        subset.close()
        return True
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def download_coastwatch_daily_by_day(
    c_date,
    bbox: tuple[float, float, float, float] | None,
    output_folder: str,
    output_filename: str | None = None,
) -> bool:
    """Download CoastWatch SMAP NRT daily-mean SSS for one calendar day.

    Args:
        c_date: Target ``datetime.date``.
        bbox: Optional ``(lon_min, lat_min, lon_max, lat_max)`` subset in degrees.
        output_folder: Directory where the NetCDF file should be saved.
        output_filename: Optional local filename expected by the dashboard.

    Returns:
        True when the file exists locally after the download attempt.
    """
    from io_utils.dates_utils import get_day_of_year_from_month_and_day

    day_of_year = get_day_of_year_from_month_and_day(c_date.month, c_date.day, c_date.year)
    return download_coastwatch_daily_single_day(
        c_date.year,
        day_of_year,
        output_folder,
        bbox=bbox,
        output_filename=output_filename,
    )


def download_coastwatch_daily_by_month(
    year: int,
    month: int,
    bbox: tuple[float, float, float, float] | None,
    output_folder: str,
) -> bool:
    """Download CoastWatch SMAP NRT daily-mean SSS for each day in a month.

    Args:
        year: Calendar year.
        month: Calendar month ``1..12``.
        bbox: Optional ``(lon_min, lat_min, lon_max, lat_max)`` subset in degrees.
        output_folder: Base directory for downloaded files.

    Returns:
        True when every day in the month downloaded successfully.
    """
    from io_utils.dates_utils import get_days_from_month

    month_folder = join(output_folder, f"{year}-{month:02d}")
    create_folder(month_folder)
    _, days_of_year = get_days_from_month(month, year)

    success = True
    for day_of_year in days_of_year:
        result = download_coastwatch_daily_single_day(
            year,
            int(day_of_year),
            month_folder,
            bbox=bbox,
        )
        success = success and result
    return success


def download_coastwatch_daily_by_year(
    year: int,
    bbox: tuple[float, float, float, float] | None,
    output_folder: str,
) -> bool:
    """Download CoastWatch SMAP NRT daily-mean SSS for each month in a year.

    Args:
        year: Calendar year.
        bbox: Optional ``(lon_min, lat_min, lon_max, lat_max)`` subset in degrees.
        output_folder: Base directory for monthly subfolders.

    Returns:
        True when every month downloaded successfully.
    """
    success = True
    for month in range(1, 13):
        result = download_coastwatch_daily_by_month(year, month, bbox, output_folder)
        success = success and result
    return success


def download_single_day(
    c_year: int,
    c_day: int,
    c_output_folder: str,
    output_filename: str | None = None,
) -> bool:
    """
    Download SSS data for a single day of year.

    Tries REMSS v06 first, then falls back to v05. Files are written directly
    into ``c_output_folder`` using the dashboard filename when provided.

    Parameters
    ----------
    c_year : int
        Calendar year.
    c_day : int
        Day of year (1-366).
    c_output_folder : str
        Directory where the NetCDF file should be saved.
    output_filename : str | None
        Optional local filename expected by the dashboard.

    Returns
    -------
    bool
        True when the file exists locally after the download attempt.
    """
    create_folder(c_output_folder)

    if output_filename is None:
        output_filename = f"RSS_smap_SSS_L3_8day_running_{c_year}_{c_day:03d}_FNL_v05.0.nc"

    output_file = join(c_output_folder, output_filename)
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return True

    for version in ("06", "05"):
        remote_name = f"RSS_smap_SSS_L3_8day_running_{c_year}_{c_day:03d}_FNL_v{version}.0.nc"
        url = (
            f"https://data.remss.com/smap/SSS/V{version}.0/FINAL/L3/8day_running/"
            f"{c_year}/{remote_name}"
        )
        if _download_remss_file(url, output_file):
            return True

    return False


def download_by_day(c_date, output_folder, output_filename: str | None = None) -> bool:
    """
    Download SMAP SSS data for a single calendar day.

    Parameters
    ----------
    c_date : datetime.date
        Target date.
    output_folder : str
        Directory where the NetCDF file should be saved.
    output_filename : str | None
        Optional local filename expected by the dashboard.

    Returns
    -------
    bool
        True when the file exists locally after the download attempt.
    """
    from io_utils.dates_utils import get_day_of_year_from_month_and_day

    c_year = c_date.year
    c_day = get_day_of_year_from_month_and_day(c_date.month, c_date.day, c_year)
    return download_single_day(c_year, c_day, output_folder, output_filename=output_filename)


def download_by_month(year: int, month: int, output_folder: str) -> bool:
    """
    Download SMAP SSS data for all days in a single month.

    Parameters
    ----------
    year : int
        Calendar year.
    month : int
        Calendar month.
    output_folder : str
        Base directory where yearly subfolders are created.

    Returns
    -------
    bool
        True when every day in the month downloaded successfully.
    """
    c_output_folder = join(output_folder, str(year))
    create_folder(c_output_folder)

    from io_utils.dates_utils import get_days_from_month

    _, days_of_year = get_days_from_month(month, year)

    success = True
    for c_day in days_of_year:
        res = download_single_day(year, int(c_day), c_output_folder)
        success = success and res
    return success


def download_by_year(year: int, output_folder: str) -> bool:
    """
    Download SMAP SSS data for all days in a single year.

    Parameters
    ----------
    year : int
        Calendar year.
    output_folder : str
        Base directory where the yearly subfolder is created.

    Returns
    -------
    bool
        True when every day in the year downloaded successfully.
    """
    c_output_folder = join(output_folder, str(year))
    create_folder(c_output_folder)

    success = True
    for c_day in range(1, 366):
        res = download_single_day(year, c_day, c_output_folder)
        success = success and res
    return success


def parallel_sss_download(output_folder: str, years: list[int], proc_id: int = 0, tot_proc: int = 1) -> None:
    """
    Download SSS data for multiple years, optionally parallelized across processes.

    Parameters
    ----------
    output_folder : str
        Base directory where yearly subfolders are created.
    years : list[int]
        Years to download.
    proc_id : int
        Process index used to shard day-of-year downloads.
    tot_proc : int
        Total number of parallel processes.
    """
    for c_year in years:
        c_output_folder = join(output_folder, str(c_year))
        create_folder(c_output_folder)

        for c_day in range(1, 366):
            if c_day % tot_proc == proc_id:
                download_single_day(c_year, c_day, c_output_folder)

    print("Done!")
