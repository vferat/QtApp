from functools import wraps
import threading
import time

import numpy as np
import mne
from mne.io.meas_info import create_info
from pycrostates.clustering import ModKMeans
from mne.preprocessing import ICA

import pylsl
from pylsl import resolve_stream, StreamInlet

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

def get_available_streams():
    print('update streams')
    return(resolve_stream())
        
available_streams = []
inlet = None
info = None
data = None
connected = False
restingstate_data = None
ica = None
modK = None

streams = get_available_streams()
print('Connecting..')
inlet_EGG = StreamInlet(streams[0])
info = _create_info(inlet_EGG)
data = np.empty((len(info['ch_names']), 0))
info.set_montage('standard_1005', on_missing='warn')
print(inlet_EGG.time_correction())
print(info)
inlet_events = StreamInlet(streams[1])
print(inlet_events.time_correction())
print('Connected..')
input('Start')
while True:
    #print(inlet_EGG.time_correction())
    #print(inlet_events.time_correction())
    
    current_time = time. time()
    samples_EEG, timestamps_EEG = inlet_EGG.pull_chunk()
    sample_events, timestamp_events = inlet_events.pull_chunk()
    print(np.array(timestamps_EEG) + inlet_EGG.time_correction())
    print(np.array(timestamp_events) + inlet_events.time_correction())
    
    time.sleep(0.05)

resting_state_raw = mne.io.RawArray(data[:, -int(resting_state_duration * info['sfreq']):],
                                    info, verbose=False)
resting_state_raw.save('resting_state_raw-raw.fif', overwrite=True)

ica= ICA(n_components=12, verbose=False)
ica = ica.fit(resting_state_raw)
ica.plot_components()
ica.save('resting_state_ica-ica.fif')
ica_resting_state_raw = ica.apply(resting_state_raw)
modK = ModKMeans(n_clusters=4)
modK.fit(ica_resting_state_raw)
modK.plot_cluster_centers()

training_duration_ = 60
data = np.empty((len(info['ch_names']), 0))
start_time = time.time()
while True:
    current_time = time. time()
    elapsed_time = current_time - start_time
    if elapsed_time > training_duration_:
        break
    samples, timestamps = inlet.pull_chunk()
    samples = np.array(samples)
    if timestamps:
        data = np.hstack([data, samples.T])
    try:    
        training_raw = mne.io.RawArray(data[:, -int(3 * info['sfreq']):],
                                        info, verbose=False)
        seg = modK.predict(training_raw)
        print(len(np.argwhere(seg == 1)) / len(seg))
    except Exception as e:
        print(e)