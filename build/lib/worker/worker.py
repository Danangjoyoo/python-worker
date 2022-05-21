import inspect
import os, time, sys, threading, ctypes, signal, keyboard, asyncio
from typing import Any, Optional, Union, overload, Type
from types import FunctionType
from .__workerhelp import help_msg

ThreadedFunction = Type["ThreadedFunction"]
AsyncThreadedFunction = Type["AsyncThreadedFunction"]

class ThreadWorker():
    """
    ThreadWorker class -> worker

    Return a worker object that behave as a thread running on background
    """

    def __init__(self, func, name="", on_abort=None, enable_keyboard_interrupt=True):
        if not name: name = "worker"
        if name in ThreadWorkerManager.allWorkers:
            name += str(ThreadWorkerManager.counts)
        ThreadWorkerManager.allWorkers[name] = self
        ThreadWorkerManager.counts += 1
        self.name = name
        self.id = ThreadWorkerManager.counts
        self.func = None
        self.rawfunc = func
        self.__finishStat = False
        self.__ret = None
        self.thread = None
        self.is_aborted = False
        self.id_mark = f"[id={self.id}][{self.name}]"
        self.aborted_by_kbInterrupt = False
        self.enable_keyboard_interrupt = enable_keyboard_interrupt
        self.on_abort = on_abort
        self.start_time = time.perf_counter()
        self.__work_time = 0
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(self.rawfunc):
            async def work_func():
                return await self.rawfunc(*args, **kwargs)
            self.func = work_func
        else:
            self.func = lambda: self.rawfunc(*args, **kwargs)
        self.work()
        return self

    ## Properties ---------------------------
    def __get_working_time(self):
        t = time.perf_counter()-self.start_time
        lst = len(str(t).split(".")[0])
        if lst < 10:
            return round(t, 10-lst)
        else:
            return int(t)

    @property
    def work_time(self):
        if self.thread and not self.finished:
            self.__work_time = self.__get_working_time()
        return self.__work_time

    @property       
    def finished(self):
        return self.__finishStat

    @property
    def ret(self):
        return self.__ret

    @property
    def is_alive(self):
        return self.thread.is_alive()

    ## Private Executor ---------------------------
    def __execute(self):
        """
        Setup and Execute the function in the background
        """
        try:
            self.__finishStat = False
            if self.func:
                self.__ret = self.func()
            else:
                self.__ret = self.rawfunc()
            self.__finishStat = True
        finally:
            self.__work_time = self.__get_working_time()
            if not self.__finishStat:
                self.__finishStat = True
                try:
                    if self.aborted_by_kbInterrupt: print(self.id_mark,"KeyboardInterrupt", flush=True)
                    if self.on_abort:
                        self.on_abort()
                except Exception as e:                      
                    print(self.id_mark,"OnAbortError",str(type(self.on_abort)), flush=True)
    
    async def __aexecute(self):
        """
        Setup and Execute the asynchronous function in the background
        """
        try:
            self.__finishStat = False
            if self.func:
                self.__ret = await self.func()
            else:
                self.__ret = await self.rawfunc()
            self.__finishStat = True
        finally:
            self.__work_time = self.__get_working_time()
            if not self.__finishStat:
                self.__finishStat = True
                try:
                    if self.aborted_by_kbInterrupt: print(self.id_mark,"KeyboardInterrupt", flush=True)
                    if self.on_abort:
                        self.on_abort()
                except Exception as e:                      
                    print(self.id_mark,"OnAbortError",str(type(self.on_abort)), flush=True)

    def work(self):
        """
        Execute function
        """
        if inspect.iscoroutinefunction(self.rawfunc):
            self.thread = threading.Thread(target=lambda: asyncio.run(self.__aexecute()))
            self.thread.start()
        else:
            self.thread = threading.Thread(target=self.__execute)
            self.thread.start()

    def interrupt(self):
        """
        Interrupt whenever signal SIGINT is raised
        """
        if self.enable_keyboard_interrupt:
            self.abort()

    def abort(self):
        """
        Abort the running worker
        """
        if self.thread:
            self.is_aborted = True
            ThreadWorkerManager.abort_thread(self.thread)

    def wait(self):
        """
        Wait the worker to finish
        """
        if self.is_alive:
            while not self.finished: time.sleep(0.005)
            return True
        return False

    def await_worker(self) -> Any:
        """
        wait the worker to finish and get it returns
        """
        self.wait()
        return self.__ret

    def restart(self):
        """
        restart the running worker with the same arguments
        """
        self.abort()
        self.start_time = time.perf_counter()
        return self()

    def __destroy(self):
        try:
            self.abort()
            del ThreadWorkerManager.allWorkers[self.name]
        except Exception as e:
            pass

class StaticThreadWorkerManager():
    """
    ThreadWorker Manager.

    Class to manage your worker and thread (abort, list, monitor)
    """
    allWorkers = {}
    counts = 0
    interrupt_timeout = 10
    keyboard_interrupt_handler_status = False

    @staticmethod
    def create_worker(*margs,**kargs):
        on_abort = None
        interrupt = True		
        if kargs:
            if "on_abort" in kargs: 
                on_abort = kargs["on_abort"]
            if "keyboard_interrupt" in kargs: 
                interrupt = bool(kargs["keyboard_interrupt"])
            if "interrupt" in kargs: 
                interrupt = bool(kargs["interrupt"])
            if not margs: 
                e = "Error: on_abort requires worker name on decorator\nPlease read ThreadWorkerManager.help()"
                raise Exception(e)
        if margs:
            if type(margs[0]) == FunctionType:
                assert not inspect.iscoroutinefunction(margs[0]), "please use `async_worker` instead for coroutine function"
                def register(*args,**kargs):
                    w = ThreadWorker(
						lambda: margs[0](*args,**kargs),
						"worker", 
						on_abort, interrupt)
                    w.work()
                    return w
                return register
            elif type(margs[0]) == str:
                def applying(func):
                    assert not inspect.iscoroutinefunction(func), "please use `async_worker` instead for coroutine function"
                    def register(*args,**kargs):
                        workerName = margs[0]
                        w = ThreadWorker(
                            lambda: func(*args,**kargs),
                            workerName,
                            on_abort, interrupt)
                        w.work()
                        return w                        
                    return register
                return applying
            else:
                return ThreadWorkerManager._workerDefinitionError()
        else:
            return ThreadWorkerManager._workerDefinitionError()
    
    @staticmethod
    def create_async_worker(*margs,**kargs):
        on_abort = None
        interrupt = True		
        if kargs:
            if "on_abort" in kargs: 
                on_abort = kargs["on_abort"]
            if "keyboard_interrupt" in kargs: 
                interrupt = bool(kargs["keyboard_interrupt"])
            if "interrupt" in kargs: 
                interrupt = bool(kargs["interrupt"])
            if not margs: 
                e = "Error: on_abort requires worker name on decorator\nPlease read ThreadWorkerManager.help()"
                raise Exception(e)
        if margs:
            if type(margs[0]) == FunctionType:
                assert inspect.iscoroutinefunction(margs[0]), "please use `worker` instead for non-coroutine function"
                async def register(*args,**kargs):
                    async def worker_func():
                        return await args[0](*args,**kargs)
                    w = ThreadWorker(
						worker_func,
						"worker", 
						on_abort, interrupt)
                    w.work()
                    return w
                return register
            elif type(margs[0]) == str:
                def applying(func):
                    assert inspect.iscoroutinefunction(func), "please use `worker` instead for non-coroutine function"
                    async def register(*args,**kargs):
                        workerName = margs[0]
                        async def worker_func():
                            return await func(*args,**kargs)
                        w = ThreadWorker(
                            worker_func,
                            workerName,
                            on_abort, interrupt)
                        w.work()
                        return w
                    return register
                return applying
            else:
                return ThreadWorkerManager._workerDefinitionError()
        else:
            return ThreadWorkerManager._workerDefinitionError()

    @staticmethod
    def _workerDefinitionError():
        e = "Error: Worker Decorator function or method! Please read ThreadWorkerManager.help()"
        raise Exception(e)

    @staticmethod
    def run_as_worker(
            target: FunctionType,
            *function_args,
            _worker_name: Optional[str] = "",
            _worker_on_abort: Optional[FunctionType] = None,
            _keyboard_interrupt: bool =True,
            args: Optional[Union[list, tuple]] = (),
            kargs: Optional[dict] = {},
            **function_kargs
        ) -> ThreadedFunction:
        """
        Run your existed function that is not defined as a worker to behave like worker
        """
        args = list(args)+list(function_args)
        kargs.update(function_kargs)
        @ThreadWorkerManager.create_worker(_worker_name,on_abort=_worker_on_abort,keyboard_interrupt=_keyboard_interrupt)
        def runFunction():
            return target(*args,**kargs)
        return runFunction()

    @staticmethod
    def run_as_async_worker(
            target: FunctionType,
            *function_args,
            _worker_name: Optional[str] = "",
            _worker_on_abort: Optional[FunctionType] = None,
            _keyboard_interrupt: bool =True,
            args: Optional[Union[list, tuple]] = (),
            kargs: Optional[dict] = {},
            **function_kargs
        ) -> AsyncThreadedFunction:
        """
        Run your existed function that is not defined as a worker to behave like worker
        """
        args = list(args)+list(function_args)
        kargs.update(function_kargs)
        @ThreadWorkerManager.create_async_worker(_worker_name,on_abort=_worker_on_abort,keyboard_interrupt=_keyboard_interrupt)
        def runFunction():
            return target(*args,**kargs)
        return runFunction()

    @staticmethod
    def wait(*workers: ThreadWorker, wait_all: bool = False):
        """
        wait defined workers to be done
        """
        if wait_all: workers = ThreadWorkerManager.allWorkers.values()
        for w in workers: w.wait()
    
    @staticmethod
    def await_workers(*workers: ThreadWorker, await_all: bool = False) -> dict:
        """
        await defined workers to be done and return a dict of results
        """
        if await_all: workers = ThreadWorkerManager.allWorkers.values()
        res = {}
        for w in workers:
            res[w.name] = w.await_worker()
        return res

    @staticmethod
    def list(active_only=False):
        formatStr = "{:<5}|{:<20}|{:<6}|{:<15}| {:<15}"
        lineSeparator = lambda: print("{:=<62}".format(""))
        lineSeparator()
        print(formatStr.format("ID","Name","Active","Address","WorkTime (s)"))
        lineSeparator()
        for x, key in enumerate(ThreadWorkerManager.allWorkers):
            w = ThreadWorkerManager.allWorkers[key]
            f = str(w).split(">")[0].split(' ')[3][:15]
            pline = lambda: print(formatStr.format(w.id,w.name,str(w.is_alive),f,w.work_time))
            if not active_only:
                pline()
            else:
                if w.is_alive: pline()
        lineSeparator()

    @staticmethod
    def clear():
        ThreadWorkerManager.allWorkers = {}

    @staticmethod
    def abort_thread(threadObject: threading.Thread):
        """
        Abort specific thread object
        """
        res = 0
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(threadObject.native_id, ctypes.py_object(SystemExit))
        except:
            pass
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(threadObject.ident, ctypes.py_object(SystemExit))
        except:
            pass
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(threadObject.native_id), ctypes.py_object(SystemExit))
        except:
            pass
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(threadObject.ident), ctypes.py_object(SystemExit))
        except:
            pass
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadObject.native_id), ctypes.py_object(SystemExit))
        except:
            pass
        try:
            if not res:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadObject.ident), ctypes.py_object(SystemExit))
        except:
            pass
        return res

    @staticmethod
    def abort_worker(workerObject: ThreadWorker):
        """
        Abort specific worker object
        """
        try:
            if all([forbidden not in str(workerObject.thread) for forbidden in ["MainThread","daemon"]]):
                ThreadWorkerManager.abort_thread(workerObject.thread)
        except Exception as e:
            print(e, flush=True)

    @staticmethod
    def abort_all_thread():
        """
        Abort all runnning background thread immediately.

        No matter if it's a worker or not, it will be aborted. No background thread is running.        
        """
        for th in threading.enumerate():
            if all([forbidden not in str(th) for forbidden in ["MainThread","daemon"]]):
                ThreadWorkerManager.abort_thread(th)

    @staticmethod
    def abort_all_worker(keyboard_interrupt_only=False):
        """
        Abort all active worker immeadiately

        :params keyboard_interrupt_only: bool -> enable to only abort the worker which have the keyboard interrupt enabled

        If some workers cannot aborted, it will retry the abortion for 10 times before it failing to abort.
        """
        if keyboard_interrupt_only:
            for key in ThreadWorkerManager.allWorkers:
                worker = ThreadWorkerManager.allWorkers[key]
                worker.interrupt()
        else:
            for key in ThreadWorkerManager.allWorkers:
                worker = ThreadWorkerManager.allWorkers[key]
                worker.abort()

    @staticmethod
    def restart_all():
        cw = ThreadWorkerManager.allWorkers.copy()
        for w in cw.values():
            threading.Thread(target=lambda: w.restart()).start()

    @staticmethod
    def help():
        print(help_msg)

    @staticmethod
    def interrupt_handler(sig, frame):
        timeout = False
        getAliveThreadWithInterrupt = lambda: any([ThreadWorkerManager.allWorkers[key].is_alive for key in ThreadWorkerManager.allWorkers if ThreadWorkerManager.allWorkers[key].enable_keyboard_interrupt])
        if getAliveThreadWithInterrupt():
            try:
                for key in ThreadWorkerManager.allWorkers:
                    tw = ThreadWorkerManager.allWorkers[key]
                    if tw.is_alive and tw.enable_keyboard_interrupt:
                        tw.aborted_by_kbInterrupt = True
                stat = getAliveThreadWithInterrupt()
                now = time.time()
                if stat: print("[WORKER] Aborting..", flush=True)
                while stat:
                    [ThreadWorkerManager.abort_all_worker(keyboard_interrupt_only=True) for i in range(10)]
                    stat = getAliveThreadWithInterrupt()
                    time.sleep(0.01)
                    if time.time()-now > ThreadWorkerManager.interrupt_timeout:
                        timeout = True
                        break
            finally:
                if not timeout:
                    print("\n[WORKER] All Workers Aborted", flush=True)
                else:
                    print("[WORKER] Aborting Timeout", flush=True)
        else:
            return signal.default_int_handler()

    __systemExitThread = None

    @staticmethod
    def __exitThread():
        @ThreadWorkerManager.worker("systemExit",keyboard_interrupt=False)
        def go():
            while True:
                time.sleep(0.1)
                if keyboard.is_pressed("CTRL+Z"):
                    while all([w.is_alive for w in ThreadWorkerManager.allWorkers.values()]):
                        for key in ThreadWorkerManager.allWorkers:
                            if "systemExit" not in key:
                                ThreadWorkerManager.allWorkers[key].abort()
                        time.sleep(0.1)
                        break
                    break
            ThreadWorkerManager.abort_all_thread()
        ThreadWorkerManager.__systemExitThread = go()

    @staticmethod
    def enableKeyboardInterrupt(enable_exit_thread: bool = False):
        """
        Enable the keyboard interrupt (CTRL+C) to abort the running thread

        :params enable_exit_thread: bool - set it true to activate CTRL+Z abort system
        - ex: enableKeyboardInterrupt(enable_exit_thread=True)
        """
        if not ThreadWorkerManager.keyboard_interrupt_handler_status:
            signal.signal(signal.SIGINT, ThreadWorkerManager.interrupt_handler)
            ThreadWorkerManager.keyboard_interrupt_handler_status = True
            if enable_exit_thread:
                ThreadWorkerManager.__exitThread()

    @staticmethod
    def disableKeyboardInterrupt():
        """
        Disable the keyboard interrupt (CTRL+C) to abort the running thread
        """
        if ThreadWorkerManager.keyboard_interrupt_handler_status:
            signal.signal(signal.SIGINT, signal.default_int_handler)
            ThreadWorkerManager.keyboard_interrupt_handler_status = False
            if ThreadWorkerManager.__systemExitThread:
                ThreadWorkerManager.__systemExitThread.abort()

ThreadWorkerManager = StaticThreadWorkerManager()