from .worker import *

### SHORTCUT ###
run_as_worker = ThreadWorkerManager.run_as_worker
abort_worker = ThreadWorkerManager.abort_worker
abort_all_worker = ThreadWorkerManager.abort_all_worker
abort_thread = ThreadWorkerManager.abort_thread
abort_all_thread = ThreadWorkerManager.abort_all_thread
enableKeyboardInterrupt = ThreadWorkerManager.enableKeyboardInterrupt
disableKeyboardInterrupt = ThreadWorkerManager.disableKeyboardInterrupt

@overload
def worker(function: FunctionType) -> ThreadedFunction: ...

@overload
def worker(
    name: Optional[str] = "",
    on_abort: Optional[FunctionType] = None,
    keyboard_interrupt: Optional[bool] = True
) -> ThreadedFunction: ...

@overload
def worker(
    on_abort: Optional[FunctionType] = None,
    keyboard_interrupt: Optional[bool] = True
) -> ThreadedFunction: ...

def worker(
        *args,
        name: Optional[str] = "",
        on_abort: Optional[FunctionType] = None,
        keyboard_interrupt: Optional[bool] = True,
        **kargs
    ):
    """
    A worker decorator.
    Turn a main-thread function into a background-thread function automatically

    Usage Example:
    - @worker
    - @worker("cool")
    - @worker(name="looping backapp", keyboard_interrupt=True)
    - @worker(keyboard_interrupt=True, on_abort: lambda: print("its over"))
    """
    if args:
        if type(args[0]) == FunctionType:
            assert not inspect.iscoroutinefunction(args[0]), "please use `async_worker` instead for coroutine function"
            def register(*dargs,**dkargs):
                w = ThreadWorker(lambda: args[0](*dargs,**dkargs), name, on_abort, keyboard_interrupt)
                w.work()
                return w
            return register
        elif type(args[0]) == str:
            name = args[0]
            return ThreadWorkerManager.create_worker(name, *args[1:], on_abort=on_abort, keyboard_interrupt=keyboard_interrupt, **kargs)
    else:
        return ThreadWorkerManager.create_worker(name, on_abort=on_abort, keyboard_interrupt=keyboard_interrupt, **kargs)


@overload
def async_worker(function: FunctionType) -> AsyncThreadedFunction: ...

@overload
def async_worker(
    name: Optional[str] = "",
    on_abort: Optional[FunctionType] = None,
    keyboard_interrupt: Optional[bool] = True
) -> AsyncThreadedFunction: ...

@overload
def async_worker(
    on_abort: Optional[FunctionType] = None,
    keyboard_interrupt: Optional[bool] = True
) -> AsyncThreadedFunction: ...

def async_worker(
        *args,
        name: Optional[str] = "",
        on_abort: Optional[FunctionType] = None,
        keyboard_interrupt: Optional[bool] = True,
        **kargs
    ):
    """
    async_worker(function) -> threaded-corotine-function

    An asynchronous worker decorator.
    Turn a main-thread coroutine function into a background-thread coroutine function automatically

    Usage Example:
    - @async_worker
    - @async_worker("cool")
    - @async_worker(name="looping backapp", keyboard_interrupt=True)
    - @async_worker(keyboard_interrupt=True, on_abort: lambda: print("its over"))
    """
    if args:
        if type(args[0]) == FunctionType:
            assert inspect.iscoroutinefunction(args[0]), "please use `worker` instead for non-coroutine function"
            async def register(*dargs,**dkargs):
                async def worker_func():
                    return await args[0](*dargs,**dkargs)
                w = ThreadWorker(worker_func, name, on_abort, keyboard_interrupt)
                w.work()
                return w
            return register
        elif type(args[0]) == str:
            name = args[0]
            return ThreadWorkerManager.create_async_worker(name, *args[1:], on_abort=on_abort, keyboard_interrupt=keyboard_interrupt, **kargs)
    else:
        return ThreadWorkerManager.create_async_worker(name, on_abort=on_abort, keyboard_interrupt=keyboard_interrupt, **kargs)