# python-worker
[![Downloads](https://static.pepy.tech/personalized-badge/python-worker?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/python-worker)

## Installation
```
pip install python-worker
```

## Description
A package to simplify the thread declaration directly either by using decorator or pass it through function. It also allows you to stop the running thread (worker) from any layer

---
## Basic Guide
`@worker` will define a function as a thread object once it run

```
import time
from worker import worker

@worker
def go(n, sleepDur):
  for i in range(n):
    time.sleep(sleepDur)
  print('done')

go(100, 0.1)
```
The function `go` will be running as a thread

---

## Asynchronous Guide
Well, if you have a coroutine function you can use `async_worker` instead
```
import asyncio
from worker import async_worker

@async_worker
async def go():
    print("this is inside coroutine!")
    for i in range(10):
        time.sleep(0.5)
        print(i)
    print("done!")
    return "result!"

go_worker = asyncio.run(go())
```

---

## Kill / Stop / Abort the running worker
You can abort some workers, all workers or even all threads..

### Abort specific workers
```
import time
from worker import worker, abort_worker

@worker
def go4(n=10):
    for i in range(n):
        time.sleep(1)

go4_worker = go4(10)
time.sleep(3)
abort_worker(go4_worker)
```
or just abort it from the instance
```
go4_worker.abort()
```

### Abort all workers (this only abort worker threads only)
```
from worker import abort_all_worker

abort_all_worker()
```

### Abort all threads (it will abort both all worker and non-worker threads)
```
from worker import abort_all_thread

abort_all_thread()
```
---
## Run undefined `@worker` function
```
import time
from worker import run_as_Worker

def go(n):
    ...

go_worker = run_as_Worker(target=go, args=(10,))
```

---
## Get Return Value
How to get the return of threaded function ?
```
@worker
def go(n):
    time.sleep(n)
    return "done"

go_worker = go(10)

# this will await the worker to finished and return the value

go_result = go_worker.await

# You can also use this if it's finished, dont have to await

go_result = go_worker.ret
```

##  Check/Monitor All Workers
```
from worker import ThreadWorkerManager

## all created workers
ThreadWorkerManager.list()

## All active/running workers only
ThreadWorkerManager.list(active_only=True)
```
it will return the information
```
>>> ThreadWorkerManager.list()
==============================================================
ID   |Name                |Active|Address        | WorkTime (s)
==============================================================
0    |worker              |True  |0x7fdf1a977af0 | 4.97
1    |worker1             |True  |0x7fdf1a73d640 | 4.07
2    |worker2             |True  |0x7fdf1a73d9d0 | 3.83
3    |worker3             |True  |0x7fdf1a73dd00 | 3.62
4    |worker4             |True  |0x7fdf1a74b070 | 3.38
==============================================================
```

---

## Python Interactive Shell - Keyboard Interrupt (CTRL+C)
  When you run your scripts on interactive mode
  ```
  python -i myScript.py
  ```
  you could add an abort handler with keyboard interrupt to abort your thread.

  #### Inside myScript.py

  `ThreadWorkerManager.enableKeyboardInterrupt()` allows you to abort your running workers.
  ```
  from worker import worker, ThreadWorkerManager


  # enabling abort handler for worker into keyboard interrupt (CTRL+C)

  ThreadWorkerManager.enableKeyboardInterrupt()
  ```
  You could also activate exit thread which triggered by pressing the CTRL+Z. This also added an abort handler for worker into keyboard interrupt (CTRL+C).
  ```
  ThreadWorkerManager.disableKeyboardInterrupt(enable_exit_thread=True)
  ```
  Disabling abort handler for worker into keyboard interrupt (CTRL+C).
  ```
  ThreadWorkerManager.disableKeyboardInterrupt()
  ```
  Check handler status.
  ```
  ThreadWorkerManager.keyboard_interrupt_handler_status
  ```

  You also can choose which workers are allowed to be aborted on keyboard interrupt

  #### Inside myScript.py
```
from worker import worker, ThreadWorkerManager

@worker("Uninterrupted", on_abort=lambda: print("ITS GREAT"), keyboard_interrupt=False)
def go_not_interrupted():
  i = 0
  while i < 1e3/2:
    i += 10
    print(i,"go_not_interrupted")
    time.sleep(0.001)
  return i

@worker("Interrupted", on_abort=lambda: print("ITS GREAT"), keyboard_interrupt=True)
def go_interrupted():
  i = 0
  while i < 1e3/2:
    i += 10
    print(i,"go_interrupted")
    time.sleep(0.001)
  return i

ThreadWorkerManagerManager.enableKeyboardInterrupt()
go_not_interrupted()
go_interrupted()
```
  run in your terminal
  ```
  python -i myScript.py
  ```
  press CTRL+C while the process is running and see the results.

---

## Changelog
- v1.8:
  - Refactoring codes
  - flexible `worker` declaration
- v1.9:
  - Added Asynchronous Worker for coroutine function using `@async_worker` decorator
- v1.10:
  - Added `overload` typehints for `worker` and `async_worker`
  - Added `restart` feature for worker
- future:
  - In progress developing `process` worker