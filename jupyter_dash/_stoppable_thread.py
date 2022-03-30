import ctypes
import threading


class StoppableThread(threading.Thread):
    def get_id(self):
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for thread_id, thread in threading._active.items():
            if thread is self:
                return thread_id

    def kill(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
        )
        if res == 0:
            raise ValueError(f"Invalid thread id: {thread_id}")
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), None)
            raise SystemExit("Stopping thread failure")
