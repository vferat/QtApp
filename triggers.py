from pylsl import StreamInfo, StreamOutlet # import required classes
import numpy as np
import time
info = StreamInfo(name='TriggerStream', type='Markers', channel_count=1, channel_format='int32', source_id='Example') # sets variables for object info
outlet = StreamOutlet(info) # initialize stream.


while True:
    a = np.random.randint(0,10)
    outlet.push_sample(x=[a])
    print(a)
    time.sleep(np.random.randint(10,30)/100)