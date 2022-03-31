# python-worker
[![Downloads](https://static.pepy.tech/personalized-badge/python-worker?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/python-worker)

## Installation
```
pip install python-worker
```

## Description
A package to simplify the thread declaration directly either by using decorator or pass it through function. It also allows you to stop the running thread (worker) from any layer

Developed by Danangjoyoo (c) 2020

## Repository
- [GitHub Repo](https://github.com/Danangjoyoo/python-worker)


## Examples of How To Use
`@worker` will define a function as a thread object once it run

- Simple Use
```
import time
from worker import worker

@worker
def go(n,sleepDur):
  for i in range(n):
    print('AAAA', i)
    time.sleep(sleepDur)
  print('done')

go(100, 0.1)
```
the code above is equals to
```
import time
import threading

def go(n=10,sleepDur=1):
  for i in range(n):
    print('AAAA', i)
    time.sleep(sleepDur)
  print('done')

th1 = threading.Thread(target=go, args=(100,0.1,))
th1.start()
```
  both are running `go` function as a thread. using `@worker` as decorator provide us direct access to thread

- Simple Use with worker/process name
```
import time
from worker import worker

@worker(name='worker cool')
def go1():
  for i in range(10):
    print('AAAA', i)
    time.sleep(1)
  print('done')

go1()
```
or
```
@worker('worker cool')
def go1():
  for i in range(10):
    print('AAAA', i)
    time.sleep(1)
  print('done')

go1()
```
---
## Basic Guide
Getting return, wait and stop the thread/worker

For example, we have this defined worker
```
import time
from worker import worker

def onAbortExample():
  print("this thread is aborted really cool")

@worker(name='worker cool',on_abort=onAbortExample)
def go(n,duration):
    for i in range(n):
      print('AAAA', i)
      time.sleep(duration)
    print('done')
    value = n*duration
    return value
```

- run the worker
  ```
  goWorker = go(100,0.5)
  ```
- wait the function to finish
  ```
  goWorker.wait()
  ```
- get the function return (the return would be `None` if the worker still running)
  ```
  valueTimesDuration = goWorker.ret
  ```
- or simply await for the function return
  ```
  goWorker.await_worker()
  ```
- abort/stop the running thread
  ```
  goWorker.abort()
  ```

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

## uncomment codes below to see the result
# go_worker.wait()
# go_result = go_worker
```

---

## Additional Features
Some advance features for thread/worker

- Run undefined `@worker` function
```
import time
from worker import run_as_Worker

def go4(n=1):
  i = 0
  while i < 1e3/2:
    i += n
    print(i)
    time.sleep(0.001)
  return i
```
  there are 2 methods to run these :
  1. Using simple pattern
		- simple use
			```
			go4_worker = run_as_Worker(go4,10)
			```
		- with name and on_abort
			```
			go4_worker = run_as_Worker(go4, 10, worker_name="go2 worker", worker_on_abort=lambda: print("horay"))
			```			
  2. using `threading.Thread()` pattern
```
go4_worker = run_as_Worker(target=go4, args=(10,), worker_name="go2 worker", worker_on_abort=lambda: print("horay"))
```
  
- Check workers
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
>>> ThreadWorkerManager.list()
==============================================================
ID   |Name                |Active|Address        | WorkTime (s)   
==============================================================
0    |worker              |True  |0x7fdf1a977af0 | 7.19           
1    |worker1             |True  |0x7fdf1a73d640 | 6.29           
2    |worker2             |True  |0x7fdf1a73d9d0 | 6.06           
3    |worker3             |True  |0x7fdf1a73dd00 | 5.84           
4    |worker4             |True  |0x7fdf1a74b070 | 5.6            
==============================================================
```


- abort specific workers
```
import time
from worker import worker, abort_worker

def go4(n=1):
  i = 0
  while i < 1e6/2:
    i += n
    print(i)
    time.sleep(0.1)
  return i

go4_worker = go4(10)
time.sleep(3)
abort_worker(go4_worker)
```

- abort all workers (this only abort worker threads only)
  ```
  from worker import abort_all_worker

  # input all your workers here

  # abort all of it
  abort_all_worker()

  ```
  
- abort all threads (it will abort both all worker and non-worker threads)
  ```
  from worker import abort_all_worker

  # input all your threads here (including)

  # abort all of it
  abort_all_thread()
  ```

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
- future:
  - In progress developing `process` worker