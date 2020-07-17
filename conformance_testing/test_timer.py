import threading


class TestTimer(threading.Thread):
    """
    Timer that rises a TimeOut Exeption after a given period of time.
    """
    def __init__(self, callback, timeout=30):
        super().__init__()
        self.timeout = timeout
        self.callback = callback
        self._timer = threading.Timer(self.timeout, self.callback)
        self._started = False

    def start_timer(self):
        if not self._started:
            self._timer.start()
            self._started = True

    def reset_timer(self):
        if not self._started:
            self._timer.start()
            self._started = True
        else:
            self._timer.cancel()
            self._timer = threading.Timer(self.timeout, self.callback)
            self._timer.start()


