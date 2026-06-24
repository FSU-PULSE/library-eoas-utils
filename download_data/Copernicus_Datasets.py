"""Copernicus Marine dataset identifiers and metadata for download scripts."""

from enum import Enum


class Copernicus_Enum(Enum):
    """Catalog keys for supported Copernicus Marine products.

    Naming convention: ``FIELD_Lx_SENSOR_RES_YEAR`` (or ``FIELD_Lx_RES_YEAR``
    for multi-sensor composites). Member doc URLs point to product pages.
    """
    # Ch
    CHLORA_L3_OLCI_300M_2016 = 0 # https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L3_MY_009_103/description
    CHLORA_L3_OLCI_4KM_2016 = 1 # https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L3_MY_009_103/description
    CHLORA_L4_D_1997 = 2 # https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L4_MY_009_104/description

    SST_ODYSSEA_L3_P1D_2021 = 20 # https://data.marine.copernicus.eu/product/SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010/description
    SST_ODYSSEA_L3_P1D_1982 = 22 # https://data.marine.copernicus.eu/product/SST_GLO_PHY_L3S_MY_010_039/description
    SST_OSTIA_L4_D = 21 # https://data.marine.copernicus.eu/product/SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001/description

    SSH_DUACS_L4_D_2022 = 30 # https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description
    SSH_DUACS_L4_D_1993 = 31 # https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_MY_008_047/description
    SSH_DUACS_L3_D_SWATHS_2022 = 32 # https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L3_NRT_008_044/description

# Metadata dict keyed by :class:`Copernicus_Enum` for use with ``copernicusmarine.subset``.
Copernicus_Datasets = {
    Copernicus_Enum.SSH_DUACS_L4_D_2022: {
        'name': 'Global Ocean Gridded L4 Sea Surface Heights And Derived Variables NRT',
        'short_name': 'SSH_DUACS_L4_NRT',
        'id': 'cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D',
        'version': '202506',
        'start_date': '2022-01-01',
        'end_date': 'Current',
        'resolution': '0.125x0.125',
        'variables': ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "ugos", "ugosa", "vgos", "vgosa"],
    },
    Copernicus_Enum.SSH_DUACS_L4_D_1993: {
        'name': 'Global Ocean Gridded L 4 Sea Surface Heights And Derived Variables Reprocessed 1993',
        'short_name': '', 
        'id': "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
        'version':'202411',
        'start_date':"1993-01-01",
        'end_date':"Sep 2023",
        'resolution':'0.25x0.25',
        'variables': ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "tpa_correction", "ugos", "ugosa", "vgos", "vgosa"],
    },
    Copernicus_Enum.SSH_DUACS_L3_D_SWATHS_2022: {
        'name': 'Global Ocean Along Track L 3 Sea Surface Heights Nrt',
        'short_name': 'SSH_DUACS_L3_D_SWATHS_2022', 
        'id': "cmems_obs-sl_glo_phy-ssh_nrt_al-l3-duacs_PT1S",
        'version':'202112',
        'start_date':"2022-01-01",
        'end_date':'Current',
        'resolution':'7km',
        'variables': ["adt",  "sla"],
    },
    Copernicus_Enum.CHLORA_L3_OLCI_300M_2016: {
        'name': 'Global Ocean Colour, Bio-Geo-Chemical, L3 (daily) from Satellite Observations (1997-ongoing)',
        'short_name': 'Ocean_Color_L3_OLCI_300M',
        'id': 'cmems_obs-oc_glo_bgc-plankton_my_l3-olci-300m_P1D',
        'version': '202211',
        'start_date': '2016-04-01',
        'resolution': '300m 0.0027',
        'variables': ["CHL", "CHL_uncertainty"],
    },
    Copernicus_Enum.CHLORA_L3_OLCI_4KM_2016: {
        'name': 'Global Ocean Colour, Bio-Geo-Chemical, L3 (daily) from Satellite Observations (1997-ongoing)',
        'short_name': 'Ocean_Color_L3_OLCI_4km',
        'id': 'cmems_obs-oc_glo_bgc-plankton_my_l3-olci-4km_P1D',
        'version': '202207',
        'start_date': '2016-04-01',
        'resolution': '4km 0.036',
        'variables': ["CHL", "CHL_uncertainty"],
    },

    Copernicus_Enum.CHLORA_L4_D_1997: {
        'name': 'Global Ocean Colour (Copernicus-GlobColour), Bio-Geo-Chemical, L4 (monthly and interpolated) from Satellite Observations (1997-ongoing)',
        'short_name': 'Ocean_Color',
        'id': 'cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D',
        'version': '202311',
        'start_date': '1997',
        'resolution': '4km 0.036',
        'variables': ["CHL", "CHL_uncertainty"],
    },
    Copernicus_Enum.SST_ODYSSEA_L3_P1D_2021: {
        'name': 'ODYSSEA Global Ocean - Sea Surface Temperature Multi-sensor L3 Observations',
        'short_name': 'ODYSSEA_SST_L3_P1D',
        'id': 'IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE',
        'version': '202211',
        'start_date': '2021-01-01',
        'resolution': '0.1x0.1',
        'variables': ["adjusted_sea_surface_temperature", "bias_to_reference_sst", "or_latitude", "or_longitude", "sea_surface_temperature", "sst_dtime"],
    },
    Copernicus_Enum.SST_ODYSSEA_L3_P1D_1982: {
        'name': 'Global High Resolution ODYSSEA Sea Surface Temperature Multi-sensor L3 Observations',
        'short_name': 'ODYSSEA_SST_L3_P1D_1982',
        'id': 'cmems_obs-sst_glo_phy_my_l3s_P1D-m',
        'version': '202311',
        'start_date': '1982-01-01',
        'end_date': '2022-12-31',
        'resolution': '0.1x0.1',
        'variables': ["adjusted_sea_surface_temperature", "bias_to_reference_sst", "quality_level", "sea_surface_temperature", "sses_bias", "sses_standard_deviation", "sst_dtime"]
    },
    Copernicus_Enum.SST_OSTIA_L4_D: {
        'name': 'Global Ocean OSTIA Sea Surface Temperature and Sea Ice Analysis',
        'short_name': 'OSTIA_SST',
        'id': 'METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2',
        'version': '',
        'start_date': '2007-01-01',
        'resolution': '0.05x0.05',
        'variables': ["analysed_sst", "analysis_error", "mask", "sea_ice_fraction"],
    },
}
