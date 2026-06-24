"""Enumerations shared by EOAS visualization utilities."""

from enum import Enum


class PlotMode(Enum):
    """Raster, contour, or combined map rendering modes."""

    RASTER = 1   # Only plot the image (raster)
    CONTOUR = 2  # Only plot the contours
    MERGED = 3   # Plot raster and contours


class BackgroundType(Enum):
    """Background basemap options for ``EOAImageVisualizer``."""

    BLUE_MARBLE_LR = 1
    BLUE_MARBLE_HR = 2
    BATHYMETRY = 3
    TOPO = 4
    CARTO_DEF = 5
    BLACK = 6
    WHITE = 7
    GREY = 8
    NONE = 100
