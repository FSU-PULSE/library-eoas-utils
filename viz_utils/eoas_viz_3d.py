"""Interactive Plotly 3-D surface and scatter plots for volumetric masks."""

from os.path import join

import SimpleITK as sitk

import plotly
import plotly.figure_factory as ff
import plotly.graph_objs as go
import numpy as np
from skimage import measure


class ImageVisualizer3D:
    """Plotly-based 3-D visualizer for binary volumes and ITK images.

    Attributes are set via constructor kwargs and exposed through dynamic
    ``_attribute`` storage (see ``__getattr__`` / ``__setattr__``).
    """

    _output_folder = 'output_medical'
    _open_browser = False
    _COLORS = ['y', 'r', 'c', 'b', 'g', 'w', 'k', 'y', 'r', 'c', 'b', 'g', 'w', 'k']

    def __init__(self, **kwargs):
        """Accept optional overrides such as ``output_folder`` and ``open_browser``."""
        for arg_name, arg_value in kwargs.items():
            self.__dict__["_" + arg_name] = arg_value

    def __getattr__(self, attr):
        """Return private backing attributes for property-style access."""
        return self.__dict__["_" + attr]

    def __setattr__(self, attr, value):
        """Store values on private ``_attr`` fields."""
        self.__dict__["_" + attr] = value

    def _check_file_name(self, file_name: str) -> str:
        """Ensure Plotly HTML output file names end with ``.html``."""
        return file_name if file_name.find('html') != -1 else F'{file_name}.html'

    def plot_surface_itk(self, ctr_np, title: str = '', file_name: str = '') -> None:
        """Render a 3-D surface from a SimpleITK image volume.

        Args:
            ctr_np: SimpleITK image converted internally with ``GetArrayFromImage``.
            title: Plot title.
            file_name: Output HTML file name (``.html`` appended when missing).
        """
        self.plot_surface_np(sitk.GetArrayFromImage(ctr_np), title=title, file_name=file_name)

    def plot_surface_np(self, ctr_np: np.ndarray, title: str = '', file_name: str = '') -> None:
        """Render a 3-D triangulated surface from a binary numpy volume.

        Args:
            ctr_np: 3-D array; values above the marching-cubes threshold are
                treated as inside the surface (isovalue 0.8).
            title: Plot title.
            file_name: Output HTML file name.

        Side effects:
            Writes an HTML file under :attr:`output_folder` and optionally opens
            the browser when :attr:`open_browser` is ``True``.
        """
        # Computes marching cubes to obtain a mesh
        print('\tMarching cubes...')
        vertices, simplices, normals, values = measure.marching_cubes_lewiner(ctr_np, .8)
        print('\tDone!')

        print('\t3D Surface...')
        x, y, z = zip(*vertices)
        camera = dict(up=dict(x=1, y=0, z=0),
                      center=dict(x=0, y=0, z=0),
                      eye=dict(x=2, y=2, z=0.1))

        fig = ff.create_trisurf(x=y,
                                y=z,
                                z=x,
                                plot_edges=True,
                                color_func=None,
                                gridcolor='rgb(0,0,0)',
                                simplices=simplices,
                                show_colorbar=False,
                                title=title)

        fig['layout'].update(
            scene=dict(camera=camera),
            title=title)

        plotly.offline.plot(fig, filename=join(self.output_folder, self._check_file_name(file_name)), auto_open=self.open_browser)

    def plot_scatter_np(self, ctr_np, file_name, title=''):
        """Render a layered 3-D scatter plot of positive voxels by z-slice.

        Args:
            ctr_np: 3-D binary or label volume.
            file_name: Output HTML file name.
            title: Plot title.

        Side effects:
            Writes HTML to :attr:`output_folder`.
        """
        z, y, x = np.where(ctr_np > 0)
        data = []
        max_z = max(z)
        min_z = min(z)
        min_y = min(y)
        min_x = min(x)

        print("\tMaking data")
        for z_level in range(int(min_z), int(max_z)):
            color = 'rgb({},0,0)'.format(int(255 * (z_level - min_z) / (max_z - min_z)))
            idx = np.where(z == z_level)

            data.append(go.Scatter3d(
                x=x[idx] - min_x, y=y[idx] - min_y, z=z[idx] - min_z, hoverinfo=None,
                mode='markers', marker=dict(symbol='circle', size=2, color=color),
            ))

        tick_w = 3
        gridwidth = tick_w
        grid_color = 'rgb(150,150,150)'
        tickfont = dict(color='black', size=19, family='Old Standard TT, serif')
        titlefont = dict(color='black', size=35, family='Old Standard TT, serif')

        layout = go.Layout(
            scene=dict(
                xaxis=dict(
                    nticks=10,
                    gridwidth=gridwidth,
                    tickfont=tickfont,
                    showbackground=True,
                    backgroundcolor='rgb(255,255,255)',
                    gridcolor=grid_color,
                    titlefont=titlefont,
                ),
                yaxis=dict(
                    nticks=5,
                    gridwidth=gridwidth,
                    showbackground=True,
                    tickfont=tickfont,
                    backgroundcolor='rgb(255,255,255)',
                    gridcolor=grid_color,
                    titlefont=titlefont,
                ),
                zaxis=dict(
                    nticks=5,
                    gridwidth=gridwidth,
                    showbackground=True,
                    tickfont=tickfont,
                    backgroundcolor='rgb(255,255,255)',
                    gridcolor=grid_color,
                    titlefont=titlefont,
                ),
                aspectmode='cube',
                camera=dict(
                    up=dict(x=1, y=0, z=0),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=2, y=-3, z=1.5),
                ),
            ))

        fig = go.Figure(data=data, layout=layout)

        file_name = file_name if file_name.find('html') != -1 else F'{file_name}.html'
        fig['layout'].update(title=title)
        plotly.offline.plot(
            fig,
            filename=join(self.output_folder, self._check_file_name(file_name)),
            auto_open=self.open_browser,
        )
