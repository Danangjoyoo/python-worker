import os, time, sys, threading, ctypes, signal, keyboard
from typing import Any, Optional, Union, overload
from types import FunctionType

class ThreadWorker():
    """
    ThreadWorker class -> worker

    Return a worker object that behave as a thread running on background
    """
    allWorkers = {}
    counts = 0

    def __init__(self, name, func, on_abort=None, enable_keyboard_interrupt=True):
        self.name = name
        self.id = ThreadWorker.counts
        self.func = func
        self.__finishStat = False
        self.__ret = None
        self.thread = None
        self.is_aborted = False
        self.id_mark = f"[id={self.id}][{self.name}]"
        self.aborted_by_kbInterrupt = False
        self.enable_keyboard_interrupt = enable_keyboard_interrupt
        self.on_abort = on_abort

    @property       
    def finished(self):
        return self.__finishStat

    @property
    def ret(self):
        return self.__ret

    @property
    def is_alive(self):
        return self.thread.is_alive()

    def __execute(self):
        try:
            self.__finishStat = False
            self.__ret = self.func()
            self.__finishStat = True
        finally:
            if not self.__finishStat:
                try:
                    if self.aborted_by_kbInterrupt: print(self.id_mark,"KeyboardInterrupt", flush=True)
                    if self.on_abort:
                        self.on_abort()
                except Exception as e:                      
                    print(self.id_mark,"OnAbortError",str(type(self.on_abort)), flush=True)

    def work(self):
        self.thread = threading.Thread(target=self.__execute)
        self.thread.start()

    def interrupt(self):
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

    def __destroy(self):
        try:
            self.abort()
            del ThreadWorkerManager.allWorkers[self.name]
        except Exception as e:
            pass

class ThreadWorkerManager():
    allWorkers = {}
    counts = 0
    interrupt_timeout = 10
    keyboard_interrupt_handler_status = False

    @staticmethod
    def worker(
            *margs,
            name: str = "",
            on_abort: Optional[FunctionType] = None,
            keyboard_interrupt: bool = False,
            **kargs
        ):
        """
        worker(function) -> threaded-function

        A worker decorator.
        Turn a main-thread function into a background-thread function automatically
        """
        if margs:
            if str(type(margs[0])) == "<class 'function'>":
                if not name: name = 'worker'+str(ThreadWorkerManager.counts)
                def register(*args,**kargs):
                    ThreadWorkerManager.allWorkers[name] = ThreadWorker(
                        name, 
                        lambda: margs[0](*args,**kargs),
                        on_abort, keyboard_interrupt)
                    ThreadWorkerManager.allWorkers[name].work()
                    ThreadWorkerManager.counts += 1
                    return ThreadWorkerManager.allWorkers[name]
                return register            
        else:
            return ThreadWorkerManager._workerDefinitionError()
    
    @staticmethod
    def _workerDefinitionError():
        e = """
        Error: Worker Decorator function or method!
        Please read ThreadWorkerManager.help()
        """
        raise BaseException(e)

    @staticmethod
    def run_as_worker(
            target: FunctionType,
            *function_args,
            worker_name: Optional[str] = "",
            worker_on_abort: Optional[FunctionType] = None,
            keyboard_interrupt: bool =True,
            args: Optional[Union[list, tuple]] = (),
            kargs: Optional[dict] = {},
            **function_kargs
        ):
        """
        Run your existed function that is not defined as a worker to behave like worker
        """
        args = list(args)+list(function_args)
        kargs.update(function_kargs)
        @worker(worker_name,on_abort=worker_on_abort,keyboard_interrupt=bool(keyboard_interrupt))
        def runFunction():
            return target(*args,**kargs)
        return runFunction()

    @staticmethod
    def wait(*args):
        for i in args: i.wait()

    @staticmethod
    def list(active_only=False):
        formatStr = "{:<5}|{:<20}|{:<6}|{:<15}"
        lineSeparator = lambda: print("{:=<55}".format(""))
        lineSeparator()
        print(formatStr.format("ID","Name","Active","Address"))
        lineSeparator()
        for x, key in enumerate(ThreadWorkerManager.allWorkers):
            w = ThreadWorkerManager.allWorkers[key]
            f = str(w).split(">")[0].split(' ')[3][:15]
            pline = lambda: print(formatStr.format(w.id,w.name,str(w.is_alive),f))
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
        Abort all runnning background thread immeadiately.

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
    def help():
        with open("./help.txt") as f:
            print(f.read())

    @staticmethod
    def interrupt_handler(sig, frame):
        timeout = False
        getAliveThreadWithInterrupt = lambda: any([ThreadWorkerManager.allWorkers[key].is_alive for key in ThreadWorkerManager.allWorkers if ThreadWorker.allWorkers[key].enable_keyboard_interrupt])
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
            signal.signal(signal.SIGINT, ThreadWorker.interrupt_handler)
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

### SHORTCUT ###
worker = ThreadWorkerManager.worker
run_as_Worker = ThreadWorkerManager.run_as_worker
abort_worker = ThreadWorkerManager.abort_worker
abort_all_worker = ThreadWorkerManager.abort_all_worker
abort_thread = ThreadWorkerManager.abort_thread
abort_all_thread = ThreadWorkerManager.abort_all_thread
enableKeyboardInterrupt = ThreadWorkerManager.enableKeyboardInterrupt
disableKeyboardInterrupt = ThreadWorkerManager.disableKeyboardInterrupt