
import copy
import itertools
import warnings
from functools import partial
from numbers import Integral

import matplotlib.pyplot as plt
import matplotlib.animation as anim
from matplotlib.backends.backend_qt5agg import FigureCanvas

import mne
import numpy as np
from mne.baseline import rescale
from mne.channels.channels import _get_ch_type
from mne.channels.layout import (_find_topomap_coords, _merge_ch_data,
                                 _pair_grad_sensors)
from mne.defaults import _BORDER_DEFAULT, _EXTRAPOLATE_DEFAULT, _handle_default
from mne.io.meas_info import Info
from mne.io.pick import ( _get_channel_types, _pick_data_channels, pick_info)
from mne.utils import (logger, verbose, _check_sphere)
from mne.viz.utils import (_setup_vmin_vmax )
from mne.viz.topomap import (_check_extrapolate, _make_head_outlines,
                             _prepare_topomap, _setup_interp, _get_patch,
                             _topomap_plot_sensors, _draw_outlines)


class TopoCanvas(FigureCanvas, anim.FuncAnimation):
    '''
    This is the FigureCanvas in which the live plot is drawn.

    '''
    def __init__(self) -> None:
        self.fig, self.ax = plt.subplots()
        super().__init__(self.fig)
        self.info = None
        self.data = None
        # Call superclass constructors
        anim.FuncAnimation.__init__(self, self.fig, self._update_canvas_, interval=0.5, blit=True)
        return

    def _update_canvas_(self, i) -> None:
        self.ax.clear()
        if self.info is not None and self.data is not None:
            _plot_topomap(self.data, self.info, axes=self.ax)
        return()
    
    def _set_data(self, data):
        self.data = data


def _plot_topomap(data, pos, vmin=None, vmax=None, cmap=None, sensors=True,
                  res=12, axes=None, names=None, show_names=False, mask=None,
                  mask_params=None, outlines='head',
                  contours=6, image_interp='bilinear',
                  onselect=None, extrapolate=_EXTRAPOLATE_DEFAULT, sphere=None,
                  border=_BORDER_DEFAULT, ch_type='eeg'):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector
    sphere = _check_sphere(sphere)
    data = np.asarray(data)
    logger.debug(f'Plotting topomap for {ch_type} data shape {data.shape}')

    if isinstance(pos, Info):  # infer pos from Info object
        picks = _pick_data_channels(pos, exclude=())  # pick only data channels
        pos = pick_info(pos, picks)

        # check if there is only 1 channel type, and n_chans matches the data
        ch_type = _get_channel_types(pos, unique=True)
        info_help = ("Pick Info with e.g. mne.pick_info and "
                     "mne.io.pick.channel_indices_by_type.")
        if len(ch_type) > 1:
            raise ValueError("Multiple channel types in Info structure. " +
                             info_help)
        elif len(pos["chs"]) != data.shape[0]:
            raise ValueError("Number of channels in the Info object (%s) and "
                             "the data array (%s) do not match. "
                             % (len(pos['chs']), data.shape[0]) + info_help)
        else:
            ch_type = ch_type.pop()

        if any(type_ in ch_type for type_ in ('planar', 'grad')):
            # deal with grad pairs
            picks = _pair_grad_sensors(pos, topomap_coords=False)
            pos = _find_topomap_coords(pos, picks=picks[::2], sphere=sphere)
            data, _ = _merge_ch_data(data, ch_type, [])
            data = data.reshape(-1)
        else:
            picks = list(range(data.shape[0]))
            pos = _find_topomap_coords(pos, picks=picks, sphere=sphere)

    extrapolate = _check_extrapolate(extrapolate, ch_type)
    if data.ndim > 1:
        raise ValueError("Data needs to be array of shape (n_sensors,); got "
                         "shape %s." % str(data.shape))

    # Give a helpful error message for common mistakes regarding the position
    # matrix.
    pos_help = ("Electrode positions should be specified as a 2D array with "
                "shape (n_channels, 2). Each row in this matrix contains the "
                "(x, y) position of an electrode.")
    if pos.ndim != 2:
        error = ("{ndim}D array supplied as electrode positions, where a 2D "
                 "array was expected").format(ndim=pos.ndim)
        raise ValueError(error + " " + pos_help)
    elif pos.shape[1] == 3:
        error = ("The supplied electrode positions matrix contains 3 columns. "
                 "Are you trying to specify XYZ coordinates? Perhaps the "
                 "mne.channels.create_eeg_layout function is useful for you.")
        raise ValueError(error + " " + pos_help)
    # No error is raised in case of pos.shape[1] == 4. In this case, it is
    # assumed the position matrix contains both (x, y) and (width, height)
    # values, such as Layout.pos.
    elif pos.shape[1] == 1 or pos.shape[1] > 4:
        raise ValueError(pos_help)
    pos = pos[:, :2]

    if len(data) != len(pos):
        raise ValueError("Data and pos need to be of same length. Got data of "
                         "length %s, pos of length %s" % (len(data), len(pos)))

    norm = min(data) >= 0
    vmin, vmax = _setup_vmin_vmax(data, vmin, vmax, norm)
    if cmap is None:
        cmap = 'Reds' if norm else 'RdBu_r'

    outlines = _make_head_outlines(sphere, pos, outlines, (0., 0.))
    assert isinstance(outlines, dict)

    ax = axes if axes else plt.gca()
    _prepare_topomap(pos, ax)

    mask_params = _handle_default('mask_params', mask_params)

    # find mask limits
    extent, Xi, Yi, interp = _setup_interp(
        pos, res, extrapolate, sphere, outlines, border)
    interp.set_values(data)
    Zi = interp.set_locations(Xi, Yi)()

    # plot outline
    patch_ = _get_patch(outlines, extrapolate, interp, ax)

    # plot interpolated map
    im = ax.imshow(Zi, cmap=cmap, vmin=vmin, vmax=vmax, origin='lower',
                   aspect='equal', extent=extent,
                   interpolation=image_interp)

    # gh-1432 had a workaround for no contours here, but we'll remove it
    # because mpl has probably fixed it
    linewidth = mask_params['markeredgewidth']
    cont = True
    if isinstance(contours, (np.ndarray, list)):
        pass
    elif contours == 0 or ((Zi == Zi[0, 0]) | np.isnan(Zi)).all():
        cont = None  # can't make contours for constant-valued functions
    if cont:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter('ignore')
            cont = ax.contour(Xi, Yi, Zi, contours, colors='k',
                              linewidths=linewidth / 2.)

    if patch_ is not None:
        im.set_clip_path(patch_)
        if cont is not None:
            for col in cont.collections:
                col.set_clip_path(patch_)

    pos_x, pos_y = pos.T
    if sensors is not False and mask is None:
        _topomap_plot_sensors(pos_x, pos_y, sensors=sensors, ax=ax)
    elif sensors and mask is not None:
        idx = np.where(mask)[0]
        ax.plot(pos_x[idx], pos_y[idx], **mask_params)
        idx = np.where(~mask)[0]
        _topomap_plot_sensors(pos_x[idx], pos_y[idx], sensors=sensors, ax=ax)
    elif not sensors and mask is not None:
        idx = np.where(mask)[0]
        ax.plot(pos_x[idx], pos_y[idx], **mask_params)

    if isinstance(outlines, dict):
        _draw_outlines(ax, outlines)

    if show_names:
        if names is None:
            raise ValueError("To show names, a list of names must be provided"
                             " (see `names` keyword).")
        if show_names is True:
            def _show_names(x):
                return x
        else:
            _show_names = show_names
        show_idx = np.arange(len(names)) if mask is None else np.where(mask)[0]
        for ii, (p, ch_id) in enumerate(zip(pos, names)):
            if ii not in show_idx:
                continue
            ch_id = _show_names(ch_id)
            ax.text(p[0], p[1], ch_id, horizontalalignment='center',
                    verticalalignment='center', size='x-small')

    plt.subplots_adjust(top=.95)

    if onselect is not None:
        lim = ax.dataLim
        x0, y0, width, height = lim.x0, lim.y0, lim.width, lim.height
        ax.RS = RectangleSelector(ax, onselect=onselect)
        ax.set(xlim=[x0, x0 + width], ylim=[y0, y0 + height])
    return im, cont, interp
