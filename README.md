# python-worker


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
    both are running 'go' function as thread, using '@worker' as decorator provide us direct access to thread

- Simple Use with worker/process name
  ```
  import time
  from worker import worker

  @worker('worker cool')
  def go1():
	for i in range(10):
		print('AAAA', i)
		time.sleep(1)
	print('done')
  ```

## Basic Guide
Getting return, wait and stop the thread/worker

For example, we have this defined worker
```
import time
from worker import worker

def onAbortExample():
	print("this thread is aborted really cool")

@worker('worker cool',on_abort=onAbortExample)
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
- abort/stop the running thread
  ```
  goWorker.abort()
  ```

### NOTES 
`on_abort` and `keyboard_interrupt` arguments on `@worker` only support workers with specified name

## Advance Guide
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
  1. using `threading.Thread()` pattern
	```
	go4_worker = run_as_Worker(func=go4,args=(10,), worker_name="go2 worker", worker_on_abort=lambda: print("horay"))
	```
  
- Check workers
  ```
  from worker import ThreadWorker

  ## all created workers
  ThreadWorker.list()

  ## All active/running workers only
  ThreadWorker.list(active_only=True)
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

- python interactive - keyboard interrupt (CTRL+C)
  when you run your scripts on interactive mode
  ```
  python -i myScript.py
  ```
  you could add an abort handler with keyboard interrupt to abort your thread.

  ### Inside myScript.py

  `ThreadWorker.enableKeyboardInterrupt()` allows you to abort your running workers.
  ```
  from worker import worker, ThreadWorker


  # enabling abort handler for worker into keyboard interrupt (CTRL+C)

  ThreadWorker.enableKeyboardInterrupt()
  ```
  Disabling abort handler for worker into keyboard interrupt (CTRL+C).
  ``` 
  ThreadWorker.disableKeyboardInterrupt()
  ```
  Check handler status.
  ```
  ThreadWorker.keyboard_interrupt_handler_status
  ```

  You also can choose which worker allowed to aborted on keyboard interrupt

  Inside myScript.py
  ```
  from worker import worker, ThreadWorker
  
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


  
  ThreadWorker.enableKeyboardInterrupt()
  go_not_interrupted()
  go_interrupted()
  ```
  run in your terminal
  ```
  python -i myScript.py
  ```
  press CTRL+C while the process is running and see the results.




### NOTES AGAIN
`on_abort` and `keyboard_interrupt` arguments on `@worker` only support workers with specified name