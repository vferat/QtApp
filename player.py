from neurodecode.stream_player.stream_player import stream_player
import mne

if __name__ == '__main__':
    server_name = 'StreamPlayer'
    chunk_size = 8  # chunk streaming frequency in Hz
    raw = mne.io.read_raw_edf(r'E:\ADHD_paper_matlab_cartool\Datasets\Arns\CTRL\broadband\ArnsControls.S12000058.999999.eo.edf')
    raw.save('tmp-raw.fif', overwrite=True)
    stream_player(server_name, 'tmp-raw.fif', chunk_size)