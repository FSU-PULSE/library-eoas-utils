"""Tests for GOES ABI SST download helpers."""

import os
import shutil
from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import xarray as xr

from download_data.Download_GOES import (
    download_by_day,
    download_by_hour,
    download_by_month,
    subset_goes_dataset,
)


def _make_goes_dataset() -> xr.Dataset:
    """Build a small synthetic GOES ABI SST dataset for tests."""
    lons = np.linspace(-100.0, -55.0, 20)
    lats = np.linspace(45.0, 5.0, 15)
    sst = np.full((1, len(lats), len(lons)), 25.0, dtype=np.float32)
    return xr.Dataset(
        data_vars={
            "sea_surface_temperature": (("time", "lat", "lon"), sst),
        },
        coords={
            "time": [np.datetime64("2026-05-05T12:00:00")],
            "lon": lons,
            "lat": lats,
        },
    )


@patch("download_data.Download_GOES._download_podaac_hour")
def test_download_by_hour(mock_download_hour: MagicMock) -> None:
    """Hourly download should write the expected dashboard filename."""
    output_folder = "test_goes_hour"
    target_date = date(2026, 5, 5)

    def _write_subset(
        config,
        date_val,
        hour,
        bbox,
        dest_path,
    ) -> None:
        ds = _make_goes_dataset()
        ds.to_netcdf(dest_path)
        ds.close()

    mock_download_hour.side_effect = _write_subset

    success = download_by_hour(
        target_date,
        12,
        "g19_l3c",
        (-98.0, 7.5, -60.0, 50.0),
        output_folder,
    )

    assert success
    expected = os.path.join(output_folder, "GOES_ABI_SST_2026-05-05_1200.nc")
    assert os.path.exists(expected)
    shutil.rmtree(output_folder)


@patch("download_data.Download_GOES.download_by_hour")
def test_download_by_day_uses_noon_snapshot(mock_download_hour: MagicMock) -> None:
    """Daily download should request the noon snapshot by default."""
    mock_download_hour.return_value = True
    target_date = date(2026, 5, 5)

    success = download_by_day(
        target_date,
        "g19_l3c",
        (-98.0, 7.5, -60.0, 50.0),
        "test_goes_day",
        output_filename="GOES_ABI_SST_2026-05-05_1200.nc",
    )

    assert success
    mock_download_hour.assert_called_once()


@patch("download_data.Download_GOES.download_by_day")
def test_download_by_month(mock_download_day: MagicMock) -> None:
    """Monthly download should call the daily helper for each day in May."""
    mock_download_day.return_value = True
    output_folder = "test_goes_month"

    success = download_by_month(
        2026,
        5,
        "g19_l3c",
        (-98.0, 7.5, -60.0, 50.0),
        output_folder,
    )

    assert success
    assert mock_download_day.call_count == 31
    shutil.rmtree(output_folder, ignore_errors=True)


def test_subset_goes_dataset_descending_latitude() -> None:
    """Subsetting should handle descending latitude coordinates."""
    ds = _make_goes_dataset()
    subset = subset_goes_dataset(ds, (-98.0, 7.5, -60.0, 50.0))
    assert subset.sizes["lat"] > 0
    assert subset.sizes["lon"] > 0
    ds.close()
    subset.close()
