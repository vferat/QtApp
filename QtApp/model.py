from functools import wraps
import threading
import time

import numpy as np
import mne
from mne.io.meas_info import create_info
from pycrostates.clustering import ModKMeans
from mne.preprocessing import ICA

from pylsl import resolve_stream, StreamInlet

from qtpy.QtCore import (QObject, Signal)

class Communicate(QObject):
    data_signal = Signal(np.ndarray)


def _create_info(client):
    sfreq = client.info().nominal_srate()
    lsl_info = client.info()
    ch_info = lsl_info.desc().child("channels").child("channel")
    ch_names = list()
    ch_types = list()
    ch_type = lsl_info.type().lower()
    for k in range(1,  lsl_info.channel_count() + 1):
        ch_names.append(ch_info.child_value("label") or
                        '{} {:03d}'.format(ch_type.upper(), k))
        ch_types.append(ch_info.child_value("type").lower() or ch_type.lower)
        ch_info = ch_info.next_sibling()
    info = create_info(ch_names, sfreq, ch_types)
    return info


def data_changed(f):
    """Call self.view.data_changed method after function call."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        f(*args, **kwargs)
        args[0].view.data_changed()
    return wrapper


class Model:
    """Data model for QtApp."""
    def __init__(self):
        self.view = None  # current view
        self.available_streams = []
        self.inlet = None
        self.info = None
        self.data = None
        self.DataLoop = None
        self.connected = False
        self.mySrc = Communicate()
        # Preprocessing
        self.restingstate_data = None
        self.ica = None
        self.modK = None

    @data_changed
    def get_available_streams(self):
        print('update streams')
        self.available_streams = resolve_stream(1)

    @data_changed
    def connect(self):
        self.inlet = StreamInlet(self.available_streams[0])
        info = _create_info(self.inlet)
        info.set_montage('standard_1005', on_missing='warn')
        self.info = info
        self.data = np.empty((len(self.info['ch_names']), 0))
        self.DataLoop = threading.Thread(name = 'DataLoop', target = self.update_topo_loop, daemon = True)
        self.DataLoop.start()
        self.connected = True

    @data_changed
    def disconnect(self):
        self.DataLoop.do_run = False
        time.sleep(0.2)
        self.data = None
        self.inlet = None
        self.info = None
        self.connected = False


    def update_topo_loop(self):
        # Setup the signal-slot mechanism.
        # Simulate some data
        while True:
            samples, timestamps = self.inlet.pull_chunk()
            samples = np.array(samples)
            if timestamps:
                data = np.hstack([self.data, samples.T])
                self.data = data
                self.mySrc.data_signal.emit(data[:,-1]) # <- Here you emit a signal!
            time.sleep(0.05)

    # Resting State
    def set_restingstate_data(self):
        self.restingstate_data = mne.io.RawArray(self.data[:, -int(60 * self.info['sfreq']):],
                                                 self.info, verbose=False)
   
    @data_changed
    def make_ica(self):
        ica= ICA(n_components=12, verbose=False)
        self.ica = ica.fit(self.restingstate_data)

    @data_changed
    def run_ica(self):
        thread = threading.Thread(name='restingstate', target=self.make_ica, daemon=True)
        thread.start()

    def make_kmeans(self):
        modK = ModKMeans(n_clusters=4)
        raw = self.ica.apply(self.restingstate_data)
        modK.fit(raw)
        self.modK = modK

    @data_changed
    def run_kmeans(self):
        thread = threading.Thread(name='restingstate', target=self.make_kmeans, daemon=True)
        thread.start()


