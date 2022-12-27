import asyncio
import inspect
import json
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from types import FunctionType


class ProcessConnector:
    def __init__(self, function):
        self.parent_con, self.child_con = None, None
        self.pid = 0
        self.proc = None
        self.raw_func = function
        self.is_async = inspect.iscoroutinefunction(function)
        self.result = None

    def kill(self):
        self.proc.kill()

    def execute_in_process(self, conn: Connection):
        try:
            input_params = conn.recv()
            args = input_params.get("args", [])
            kwargs = input_params.get("kwargs", {})
            result = self.raw_func(*args, **kwargs)
            try:
                json.dumps(result)
            except Exception as e:
                print(e)
                result = {}
            conn.send(result)
        except Exception as error:
            print(error)
            raise error
        finally:
            conn.close()

    async def execute_in_process_event_loop(self, conn: Connection):
        try:
            input_params = conn.recv()
            args = input_params.get("args", [])
            kwargs = input_params.get("kwargs", {})
            result = self.raw_func(*args, **kwargs)
            try:
                json.dumps(result)
            except Exception as e:
                print(e)
                result = {}
            conn.send(result)
        except Exception as error:
            print(error)
            raise error
        finally:
            conn.close()

    def create_and_run(self, *args, **kwargs):
        self.parent_con, self.child_con = Pipe()
        if self.is_async:
            self.proc = Process(target=asyncio.run(self.execute_in_process_event_loop(self.child_con)))
        else:
            self.proc = Process(target=lambda: self.execute_in_process(self.child_con))
        self.proc.start()
        self.parent_con.send({"args": args, "kwargs": kwargs})
        return self.parent_con

    @property
    def ret(self):
        if self.parent_con and not self.parent_con.closed and self.child_con.closed:
            self.result = self.parent_con.recv()
            self.parent_con.close()
        return self.result

    def wait(self, timeout):
        self.proc.join(timeout)

    def receive(self):
        return self.parent_con.recv()

    @staticmethod
    def create_process(function: FunctionType):
        assert isinstance(function, FunctionType), "only accept function for process"
        def run_in_different_proc(*args, **kwargs):
            pc = ProcessConnector(function)
            pc.create_and_run(*args, **kwargs)
            return pc
        return run_in_different_proc
