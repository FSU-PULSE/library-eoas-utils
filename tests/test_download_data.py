import os
import shutil
from unittest.mock import patch, MagicMock
from datetime import date
from download_data.Download_SSS_SMAP_satellite import parallel_sss_download, download_by_day, download_by_month, download_by_year

@patch('download_data.Download_SSS_SMAP_satellite.requests')
def test_parallel_sss_download(mock_requests):
    # Setup mock responses to avoid hitting the actual network and speed up tests
    mock_head_response = MagicMock()
    mock_head_response.status_code = 200
    mock_head_response.headers = {'content-length': '9'}
    mock_requests.head.return_value = mock_head_response

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.content = b"mock_data"
    mock_requests.get.return_value = mock_get_response

    proc_id = 0
    TOT_PROC = 365  # By choosing 365, only day 365 will match (365 % 365 == 0)
    output_folder = "test_folder"
    years = [2020]

    # Execute
    parallel_sss_download(output_folder, years, proc_id=proc_id, TOT_PROC=TOT_PROC)

    # Verify
    year_folder = os.path.join(output_folder, "2020")
    assert os.path.exists(year_folder)
    file_name = "RSS_smap_SSS_L3_8day_running_2020_365_FNL_v05.0.nc"
    assert os.path.exists(os.path.join(year_folder, file_name))

    # Cleanup
    shutil.rmtree(output_folder)

@patch('download_data.Download_SSS_SMAP_satellite.requests')
def test_download_modes(mock_requests):
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.content = b"mode_data"
    mock_requests.get.return_value = mock_get_response

    output_folder = "test_modes_folder"

    # Test download_by_day
    c_date = date(2020, 5, 15)  # May 15 is day 136 in 2020 (leap year)
    download_by_day(c_date, output_folder)
    day_file = os.path.join(output_folder, "2020", "RSS_smap_SSS_L3_8day_running_2020_136_FNL_v05.0.nc")
    assert os.path.exists(day_file)

    # Test download_by_month (May is month 5, has 31 days)
    download_by_month(2020, 5, output_folder)
    # May 1 (day 122) and May 31 (day 152) should be present
    assert os.path.exists(os.path.join(output_folder, "2020", "RSS_smap_SSS_L3_8day_running_2020_122_FNL_v05.0.nc"))
    assert os.path.exists(os.path.join(output_folder, "2020", "RSS_smap_SSS_L3_8day_running_2020_152_FNL_v05.0.nc"))

    # Cleanup
    shutil.rmtree(output_folder)