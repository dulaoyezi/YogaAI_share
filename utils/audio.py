#异步语音播报设计，防止卡死
import pyttsx3
import threading
import pythoncom

class YogaAudio:
    def __init__(self):
        self.rate = 160

    def speak(self, text):
        t = threading.Thread(target=self._run_speech, args=(text,))
        t.daemon = True; t.start()

    def _run_speech(self, text):
        pythoncom.CoInitialize() # 线程内必须初始化
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            voices = engine.getProperty('voices')
            for v in voices:
                if "ZH" in v.id or "Chinese" in v.name:
                    engine.setProperty('voice', v.id); break
            engine.say(text); engine.runAndWait(); engine.stop()
        finally:
            pythoncom.CoUninitialize()