"""Download NOAA GOES ABI sea-surface temperature from PODAAC and CoastWatch ERDDAP.

Supports hourly, daily, monthly, and yearly retrieval modes. The default GOES-East
product is the ACSPO L3C hourly SST from GOES-19 on NASA PO.DAAC
(``ABI_G19-STAR-L3C-v3.0``), which requires Earthdata credentials in ``~/.netrc``.
"""

from __future__ import annotations

import datetime
import os
import shutil
import tempfile
from calendar import monthrange
from os.path import join

import earthaccess
import requests
import xarray as xr

from io_utils.io_common import create_folder, dotdict

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}

DEFAULT_OUTPUT_FOLDER = "./test_data/Satellite_Data_Examples/SST/GOES_ABI"

GOES_PRODUCTS: dict[str, dotdict] = {
    "g19_l3c": dotdict({
        "label": "GOES-19 ABI ACSPO L3C SST (GOES-East, PODAAC)",
        "source": "podaac",
        "short_name": "ABI_G19-STAR-L3C-v3.0",
        "var_name": "sea_surface_temperature",
        "lon_var": "lon",
        "lat_var": "lat",
    }),
    "g16_l3c": dotdict({
        "label": "GOES-16 ABI ACSPO L3C SST (GOES-East archive, PODAAC)",
        "source": "podaac",
        "short_name": "ABI_G16-STAR-L3C-v2.70",
        "var_name": "sea_surface_temperature",
        "lon_var": "lon",
        "lat_var": "lat",
    }),
    "g18_erddap": dotdict({
        "label": "GOES-18 ABI ACSPO SST (GOES-West, CoastWatch ERDDAP)",
        "source": "erddap",
        "dataset_id": "goes_west",
        "erddap_base": "https://coastwatch.pfeg.noaa.gov/erddap/griddap",
        "var_name": "sea_surface_temperature",
        "lon_var": "longitude",
        "lat_var": "latitude",
    }),
    "gom_daily_erddap": dotdict({
        "label": "GOES Daily SST (Gulf/Caribbean regional ERDDAP)",
        "source": "erddap",
        "dataset_id": "goesSST",
        "erddap_base": "https://cwcgom.aoml.noaa.gov/erddap/griddap",
        "var_name": "sst",
        "lon_var": "longitude",
        "lat_var": "latitude",
    }),
}


def _resolve_product(product_key: str) -> dotdict:
    """Return a GOES product configuration by key.

    Args:
        product_key: Key in :data:`GOES_PRODUCTS`.

    Returns:
        Product metadata ``dotdict``.

    Raises:
        KeyError: When ``product_key`` is unknown.
    """
    if product_key not in GOES_PRODUCTS:
        raise KeyError(
            f"Unknown GOES product '{product_key}'. "
            f"Valid options: {', '.join(sorted(GOES_PRODUCTS))}"
        )
    return GOES_PRODUCTS[product_key]


def _default_hourly_filename(date_val: datetime.date, hour: int) -> str:
    """Build the default hourly GOES ABI SST filename.

    Args:
        date_val: Calendar date.
        hour: Hour of day ``0..23``.

    Returns:
        NetCDF filename such as ``GOES_ABI_SST_2026-05-05_1200.nc``.
    """
    return f"GOES_ABI_SST_{date_val.year}-{date_val.month:02d}-{date_val.day:02d}_{hour:02d}00.nc"


def _default_daily_filename(date_val: datetime.date) -> str:
    """Build the default daily GOES ABI SST filename (noon snapshot).

    Args:
        date_val: Calendar date.

    Returns:
        NetCDF filename such as ``GOES_ABI_SST_2026-05-05_1200.nc``.
    """
    return _default_hourly_filename(date_val, 12)


def _default_monthly_filename(year: int, month: int) -> str:
    """Build the default monthly GOES ABI SST filename.

    Args:
        year: Calendar year.
        month: Calendar month ``1..12``.

    Returns:
        NetCDF filename such as ``GOES_ABI_SST_2026-05.nc``.
    """
    return f"GOES_ABI_SST_{year}-{month:02d}.nc"


def _default_yearly_filename(year: int) -> str:
    """Build the default yearly GOES ABI SST filename.

    Args:
        year: Calendar year.

    Returns:
        NetCDF filename such as ``GOES_ABI_SST_2026.nc``.
    """
    return f"GOES_ABI_SST_{year}.nc"


def _bbox_to_cmr(bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Convert dashboard bbox to CMR ``(west, south, east, north)`` order.

    Args:
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.

    Returns:
        Bounding box in CMR order.
    """
    return (bbox[0], bbox[1], bbox[2], bbox[3])


def subset_goes_dataset(
    ds: xr.Dataset,
    bbox: tuple[float, float, float, float],
    lon_var: str = "lon",
    lat_var: str = "lat",
) -> xr.Dataset:
    """Spatially subset a GOES ABI SST dataset to a bounding box.

    Args:
        ds: Input dataset with longitude/latitude coordinates.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        lon_var: Longitude coordinate name.
        lat_var: Latitude coordinate name.

    Returns:
        Spatially subset dataset.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    lat_values = ds[lat_var].values
    if len(lat_values) > 1 and lat_values[0] > lat_values[-1]:
        lat_slice = slice(lat_max, lat_min)
    else:
        lat_slice = slice(lat_min, lat_max)
    return ds.sel({lon_var: slice(lon_min, lon_max), lat_var: lat_slice})


def _save_subset(
    ds: xr.Dataset,
    config: dotdict,
    bbox: tuple[float, float, float, float],
    dest_path: str,
) -> None:
    """Subset a GOES dataset and write a compact NetCDF for the dashboard.

    Args:
        ds: Full or partial GOES dataset.
        config: Product configuration from :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        dest_path: Output NetCDF path.
    """
    lon_var = config.lon_var
    lat_var = config.lat_var
    var_name = config.var_name

    if lon_var not in ds.coords and "longitude" in ds.coords:
        lon_var = "longitude"
    if lat_var not in ds.coords and "latitude" in ds.coords:
        lat_var = "latitude"

    subset = subset_goes_dataset(ds, bbox, lon_var=lon_var, lat_var=lat_var)
    if var_name not in subset.variables:
        raise KeyError(f"Variable '{var_name}' not found in GOES dataset")

    keep_vars = [var_name]
    for coord_name in (lon_var, lat_var, "time"):
        if coord_name in subset.coords:
            keep_vars.append(coord_name)

    out_ds = subset[keep_vars]
    rename_map: dict[str, str] = {}
    if lon_var != "lon" and lon_var in out_ds.coords:
        rename_map[lon_var] = "lon"
    if lat_var != "lat" and lat_var in out_ds.coords:
        rename_map[lat_var] = "lat"
    if rename_map:
        out_ds = out_ds.rename(rename_map)

    out_ds.to_netcdf(dest_path)
    ds.close()


def _download_erddap_subset(
    config: dotdict,
    time_start: str,
    time_end: str,
    bbox: tuple[float, float, float, float],
    dest_path: str,
) -> None:
    """Download a GOES ERDDAP griddap subset to disk.

    Args:
        config: ERDDAP product configuration.
        time_start: ISO-8601 start time, e.g. ``2026-05-05T12:00:00Z``.
        time_end: ISO-8601 end time.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        dest_path: Local NetCDF destination path.
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    var_name = config.var_name
    url = (
        f"{config.erddap_base}/{config.dataset_id}.nc"
        f"?{var_name}%5B({time_start}):1:({time_end})%5D"
        f"%5B({lat_min}):1:({lat_max})%5D%5B({lon_min}):1:({lon_max})%5D"
    )
    response = requests.get(url, headers=HEADERS, timeout=180)
    if response.status_code != 200:
        raise RuntimeError(
            f"ERDDAP download failed for {config.dataset_id}: HTTP {response.status_code}"
        )
    with open(dest_path, "wb") as handle:
        handle.write(response.content)


def _download_podaac_hour(
    config: dotdict,
    date_val: datetime.date,
    hour: int,
    bbox: tuple[float, float, float, float],
    dest_path: str,
) -> None:
    """Download one hourly GOES ABI SST granule from PO.DAAC and subset it.

    Args:
        config: PODAAC product configuration.
        date_val: Target calendar date.
        hour: Hour of day ``0..23``.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        dest_path: Output NetCDF path.
    """
    earthaccess.login(strategy="netrc")
    start_time = f"{date_val.strftime('%Y-%m-%d')}T{hour:02d}:00:00Z"
    end_time = f"{date_val.strftime('%Y-%m-%d')}T{hour:02d}:59:59Z"

    results = earthaccess.search_data(
        short_name=config.short_name,
        bounding_box=_bbox_to_cmr(bbox),
        temporal=(start_time, end_time),
    )
    if not results:
        raise RuntimeError(
            f"No {config.short_name} granules found for {start_time} in bbox {bbox}"
        )

    temp_dir = tempfile.mkdtemp(prefix="goes_abi_download_")
    try:
        downloaded = earthaccess.download(results[:1], local_path=temp_dir)
        if not downloaded:
            raise RuntimeError(f"earthaccess failed to download granule for {start_time}")
        ds = xr.open_dataset(downloaded[0])
        _save_subset(ds, config, bbox, dest_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _combine_datasets(datasets: list[xr.Dataset]) -> xr.Dataset:
    """Concatenate multiple GOES subsets along the time dimension.

    Args:
        datasets: Non-empty list of datasets with compatible coordinates.

    Returns:
        Time-concatenated dataset.
    """
    if len(datasets) == 1:
        return datasets[0]
    return xr.concat(datasets, dim="time")


def download_by_hour(
    date_val: datetime.date,
    hour: int,
    product_key: str,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
) -> bool:
    """Download one hourly GOES ABI SST snapshot.

    Args:
        date_val: Target calendar date.
        hour: Hour of day ``0..23``.
        product_key: Key in :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the output NetCDF file.
        output_filename: Optional override for the local filename.

    Returns:
        ``True`` when the output file exists and is non-empty.
    """
    create_folder(output_folder)
    config = _resolve_product(product_key)
    dest_path = join(
        output_folder,
        output_filename or _default_hourly_filename(date_val, hour),
    )

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True

    if config.source == "podaac":
        _download_podaac_hour(config, date_val, hour, bbox, dest_path)
    elif config.source == "erddap":
        time_iso = f"{date_val.strftime('%Y-%m-%d')}T{hour:02d}:00:00Z"
        _download_erddap_subset(config, time_iso, time_iso, bbox, dest_path)
    else:
        raise ValueError(f"Unsupported GOES source: {config.source}")

    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0


def download_by_day(
    date_val: datetime.date,
    product_key: str,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
    hour: int = 12,
    all_hours: bool = False,
) -> bool:
    """Download GOES ABI SST for one calendar day.

    By default this saves the noon (12:00 UTC) snapshot. Set ``all_hours=True``
    to retrieve and merge all 24 hourly scenes into one NetCDF file.

    Args:
        date_val: Target calendar date.
        product_key: Key in :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the output NetCDF file.
        output_filename: Optional override for the local filename.
        hour: Snapshot hour used when ``all_hours`` is ``False``.
        all_hours: When ``True``, download every hour in the day.

    Returns:
        ``True`` when the requested day completed successfully.
    """
    if not all_hours:
        return download_by_hour(
            date_val,
            hour,
            product_key,
            bbox,
            output_folder,
            output_filename=output_filename or _default_hourly_filename(date_val, hour),
        )

    create_folder(output_folder)
    config = _resolve_product(product_key)
    dest_path = join(
        output_folder,
        output_filename or f"GOES_ABI_SST_{date_val.year}-{date_val.month:02d}-{date_val.day:02d}_hourly.nc",
    )

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True

    subsets: list[xr.Dataset] = []
    temp_paths: list[str] = []
    try:
        for current_hour in range(24):
            temp_path = join(output_folder, f".tmp_goes_{date_val.isoformat()}_{current_hour:02d}.nc")
            temp_paths.append(temp_path)
            if config.source == "podaac":
                _download_podaac_hour(config, date_val, current_hour, bbox, temp_path)
            else:
                time_iso = f"{date_val.strftime('%Y-%m-%d')}T{current_hour:02d}:00:00Z"
                _download_erddap_subset(config, time_iso, time_iso, bbox, temp_path)
            subsets.append(xr.open_dataset(temp_path))

        combined = _combine_datasets(subsets)
        combined.to_netcdf(dest_path)
        for subset in subsets:
            subset.close()
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0


def download_by_month(
    year: int,
    month: int,
    product_key: str,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
    hour: int = 12,
    all_days: bool = True,
) -> bool:
    """Download GOES ABI SST for each day in a month.

    Args:
        year: Calendar year.
        month: Calendar month ``1..12``.
        product_key: Key in :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for per-day NetCDF files.
        output_filename: Unused placeholder kept for API symmetry.
        hour: Snapshot hour for each day.
        all_days: When ``False``, only the first day of the month is downloaded.

    Returns:
        ``True`` when every requested day downloaded successfully.
    """
    _ = output_filename
    last_day = monthrange(year, month)[1]
    day_range = range(1, last_day + 1) if all_days else range(1, 2)
    success = True
    for day in day_range:
        date_val = datetime.date(year, month, day)
        result = download_by_day(
            date_val,
            product_key,
            bbox,
            output_folder,
            hour=hour,
        )
        success = success and result
    return success


def download_by_year(
    year: int,
    product_key: str,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str | None = None,
    hour: int = 12,
    all_months: bool = True,
) -> bool:
    """Download GOES ABI SST for each month in a calendar year.

    Args:
        year: Calendar year.
        product_key: Key in :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for per-day NetCDF files grouped by month.
        output_filename: Unused placeholder kept for API symmetry.
        hour: Snapshot hour for each day.
        all_months: When ``False``, only January is downloaded.

    Returns:
        ``True`` when every requested month downloaded successfully.
    """
    _ = output_filename
    month_range = range(1, 13) if all_months else range(1, 2)
    success = True
    for month in month_range:
        month_folder = join(output_folder, f"{year}-{month:02d}")
        result = download_by_month(
            year,
            month,
            product_key,
            bbox,
            month_folder,
            hour=hour,
        )
        success = success and result
    return success


def download_for_dashboard(
    date_val: datetime.date,
    product_key: str,
    bbox: tuple[float, float, float, float],
    output_folder: str,
    output_filename: str,
    hour: int = 12,
) -> bool:
    """Download the noon GOES ABI SST file expected by the dashboard.

    Args:
        date_val: Target calendar date.
        product_key: Key in :data:`GOES_PRODUCTS`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Directory for the output NetCDF file.
        output_filename: Dashboard filename from product metadata.
        hour: Snapshot hour, defaulting to noon UTC.

    Returns:
        ``True`` when the dashboard file exists locally.
    """
    return download_by_day(
        date_val,
        product_key,
        bbox,
        output_folder,
        output_filename=output_filename,
        hour=hour,
    )


if __name__ == "__main__":
    bbox_gom = (-98.0, 7.5, -60.0, 50.0)
    target_date = datetime.date(2026, 5, 5)
    download_by_hour(
        target_date,
        12,
        "g19_l3c",
        bbox_gom,
        DEFAULT_OUTPUT_FOLDER,
    )
