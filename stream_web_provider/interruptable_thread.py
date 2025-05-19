import ctypes
from threading import Thread


class InterruptableThread(Thread):
    """Makes the class Thread interruptable by raising an exception"""

    def __init__(self, target=None, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}

        super().__init__(target=target, args=args, kwargs=kwargs)

        self._was_interrupted: bool = False

    def interrupt(self, exception: Exception = KeyboardInterrupt):
        # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(exception))

        if ret == 0:
            raise ValueError("Invalid thread ID")

        if ret > 1:
            # Why would we notify more than one threads?
            # Because we punch a hole into C level interpreter.
            # So it is better to clean up the mess.
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

        self._was_interrupted = True

    def was_interrupted(self) -> bool:
        return self._was_interrupted
