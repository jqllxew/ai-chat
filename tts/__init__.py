import time
import wave
from tts.aliyun_tts import tts, tts_url, tts_cos


def _play_audio(fp):
    import pyaudio
    # 打开WAV文件
    wf = wave.open(fp, 'rb')
    # 初始化PyAudio
    p = pyaudio.PyAudio()
    # 打开音频流
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    # 读取数据并播放
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
    # 停止流和PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()


def speak(text):
    _p = f"audio/{int(time.time()*1000)}"
    _play_audio(tts(text, local_key=_p))


__all__ = ["tts", "tts_url", "tts_cos", "speak"]
