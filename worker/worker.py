import os, time, sys, threading, ctypes, signal


class MainThreadWorker():
	allWorkers = {}
	counts = 0
	interrupt_timeout = 10
	keyboard_interrupt_handler_status = False

	class ChildWorker():
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
			if self.is_aborted and not self.__finishStat:
				print(self.id_mark,"return is None due to aborted before finished", flush=True)
				return None
			else:
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
			self.__finishStat = True

		def work(self):
			self.thread = threading.Thread(target=self.__execute)
			self.thread.start()

		def interrupt(self):
			if self.enable_keyboard_interrupt:
				self.abort()

		def abort(self):
			if self.thread:
				self.is_aborted = True
				ThreadWorker.abort_thread(self.thread)

		def wait(self):
			while not self.finished: pass
			self.__destroy()
			return True

		def __destroy(self):
			del ThreadWorker.allWorkers[self.name]

	@staticmethod
	def worker(*margs,**kargs):
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
				return print("Error: on_abort requires worker name on decorator\nPlease read ThreadWorker.help()",flush=True)
		if margs:
			if str(type(margs[0])) == "<class 'function'>":
				def register(*args,**kargs):
					workerName = 'worker'+str(ThreadWorker.counts)
					ThreadWorker.allWorkers[workerName] = ThreadWorker.ChildWorker(
						workerName, 
						lambda: margs[0](*args,**kargs),
						on_abort, interrupt)
					ThreadWorker.allWorkers[workerName].work()
					ThreadWorker.counts += 1
					return ThreadWorker.allWorkers[workerName]
				return register
			elif type(margs[0]) == str:
				def applying(func):
					def register(*args,**kargs):
						workerName = margs[0] if margs[0] not in ThreadWorker.allWorkers.keys() else margs[0]+str(ThreadWorker.counts)
						ThreadWorker.allWorkers[workerName] = ThreadWorker.ChildWorker(
							workerName,
							lambda: func(*args,**kargs),
							on_abort, interrupt)
						ThreadWorker.allWorkers[workerName].work()
						ThreadWorker.counts += 1
						return ThreadWorker.allWorkers[workerName]
					return register
				return applying
			else:
				print('Error: Worker Decorator only support str and function!\nPlease read ThreadWorker.help()', flush=True)
				print("another possible error: on_abort, keyboard_interrupt arguments only supported for workers with specified name", flush=True)
		else:
			print('Error: Worker Decorator only support str and function!\nPlease read ThreadWorker.help()', flush=True)
			print("another possible error: on_abort, keyboard_interrupt arguments only supported for workers with specified name", flush=True)

	@staticmethod
	def run_as_Worker(target,*function_args,worker_name="",worker_on_abort=None,keyboard_interrupt=True,args=(),kargs={},**function_kargs):
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
		for x, key in enumerate(ThreadWorker.allWorkers):
			w = ThreadWorker.allWorkers[key]
			f = str(w).split(">")[0].split(' ')[3][:15]
			pline = lambda: print(formatStr.format(w.id,w.name,str(w.is_alive),f))
			if not active_only:
				pline()
			else:
				if w.is_alive: pline()
		lineSeparator()

	@staticmethod
	def clear():
		ThreadWorker.allWorkers = {}

	@staticmethod
	def abort_thread(threadObject):
		try:
			th_id = threadObject.native_id
		except:
			th_id = threadObject.ident
		return ctypes.pythonapi.PyThreadState_SetAsyncExc(th_id, ctypes.py_object(SystemExit))

	@staticmethod
	def abort_worker(workerObject):
		try:
			if all([forbidden not in str(workerObject.thread) for forbidden in ["MainThread","daemon"]]):
				ThreadWorker.abort_thread(workerObject.thread)
		except Exception as e:
			print(e, flush=True)

	@staticmethod
	def abort_all_thread():
		for th in threading.enumerate():
			if all([forbidden not in str(th) for forbidden in ["MainThread","daemon"]]):
				ThreadWorker.abort_thread(th)

	@staticmethod
	def abort_all_worker(keyboard_interrupt_only=False):
		if keyboard_interrupt_only:
			for key in ThreadWorker.allWorkers:
				worker = ThreadWorker.allWorkers[key]
				worker.interrupt()
		else:
			for key in ThreadWorker.allWorkers:
				worker = ThreadWorker.allWorkers[key]
				worker.abort()

	@staticmethod
	def help():
		global _help_message_only
		ss = _help_message_only.splitlines()
		prints = False
		for i,s in enumerate(ss[:-1]):
			if '?!@^^^' in s and s[0] == "?": 
				prints = True
				continue
			if prints: print(s[:-1])

	@staticmethod
	def interrupt_handler(sig, frame):
		timeout = False
		if any([ThreadWorker.allWorkers[key].is_alive for key in ThreadWorker.allWorkers]):
			try:
				for key in ThreadWorker.allWorkers:
					tw = ThreadWorker.allWorkers[key]
					if tw.is_alive and tw.enable_keyboard_interrupt:
						tw.aborted_by_kbInterrupt = True
				stat = any([ThreadWorker.allWorkers[key].is_alive for key in ThreadWorker.allWorkers])
				now = time.time()
				if stat: print("[WORKER] Aborting..", flush=True)
				while stat:
					[ThreadWorker.abort_all_worker(keyboard_interrupt_only=True) for i in range(10)]
					stat = any([ThreadWorker.allWorkers[key].is_alive for key in ThreadWorker.allWorkers])					
					time.sleep(0.01)
					if time.time()-now > MainThreadWorker.interrupt_timeout:
						timeout = True
						break
			finally:
				if not timeout:
					print("\n[WORKER] All Workers Aborted", flush=True)
				else:
					print("[WORKER] Aborting Timeout", flush=True)
		else:
			return signal.default_int_handler()

	@staticmethod
	def enableKeyboardInterrupt():
		signal.signal(signal.SIGINT, ThreadWorker.interrupt_handler)
		MainThreadWorker.keyboard_interrupt_handler_status = True

	@staticmethod
	def disableKeyboardInterrupt():
		signal.signal(signal.SIGINT, signal.default_int_handler)
		MainThreadWorker.keyboard_interrupt_handler_status = False

### SHORTCUT ###
ThreadWorker = MainThreadWorker()
worker = ThreadWorker.worker
run_as_Worker = ThreadWorker.run_as_Worker
abort_worker = ThreadWorker.abort_worker
abort_all_worker = ThreadWorker.abort_all_worker
abort_thread = ThreadWorker.abort_thread
abort_all_thread = ThreadWorker.abort_all_thread
enableKeyboardInterrupt = ThreadWorker.enableKeyboardInterrupt
disableKeyboardInterrupt = ThreadWorker.disableKeyboardInterrupt


_help_message_only = """

?!@^^^
######## HELP ######## HELP ######## HELP ######## HELP ######## HELP ######## HELP ########
[help]	
[help]	@worker will define a function as a thread object once it run
[help]	
[help]	---------------------------------------------------
[help]	SIMPLE USE (example)
[help]	###################################################
[help]	from worker import worker
[help]	
[help]	@worker #-> this is the threading decorator
[help]	def go():
[help]		for i in range(10):
[help]			print('AAAA', i)
[help]			time.sleep(1)
[help]		print('done')
[help]	
[help]	@worker('worker ganteng') #-> this is the threading decorator with process name
[help]	def go1():
[help]		for i in range(10):
[help]			print('AAAA', i)
[help]			time.sleep(1)
[help]		print('done')
[help]	
[help]	# on_abort -> when the worker is aborted, it will raise on_abort
[help]	# on_abort -> workername is required when using ob_abort params
[help]	@worker('worker cool',on_abort=lambda: print("its aborted!")) 
[help]	def coba():
[help]		a = go()
[help]		#-> wait() will block the next line till go() is done
[help]		a.wait()
[help]		print('HAHAHAHAHH')
[help]	
[help]	-----------------------------------------------------
[help]	AVAILABLE MODEL
[help]	#####################################################
[help]	set worker decorator only have 3 model
[help]	
[help]	++++++ model 1 ++++++
[help]	@worker
[help]	def go1():
[help]		i = 0
[help]		while 1:
[help]			i+=1
[help]			time.sleep(0.005)
[help]		return i
[help]	
[help]	++++++ model 2 ++++++
[help]	@worker("gogogo")
[help]	def go2(n=1):
[help]		i = 0
[help]		while 1:
[help]			i+=n
[help]			time.sleep(0.005)
[help]		return i
[help]	
[help]	++++++ model 3 ++++++
[help]	@worker("gogagaaaa",on_abort=lambda: print("HAHAHAHAH"))
[help]	def go3():
[help]		i = 0
[help]		while 1:
[help]			i+=1
[help]			time.sleep(0.005)
[help]		return i
[help] 
[help] 
[help] HOW TO RUN DEFINED WORKER?
[help] #####################################
[help] 
[help] go2(n=100)
[help] # or
[help] go2(100)
[help] # or
[help] a = go1()
[help] # or
[help] b = go2(300)
[help] 
[help] 
[help] 
[help] 
[help] AVAILABLE "run as worker" MODEL
[help] ##########################################################
[help] runAsWorker only works these ways
[help] 
[help] 
[help] def go4(n=1):
[help] 	i = 0
[help] 	while i < 1e3/2:
[help] 		i += n
[help] 		print(i)
[help] 		time.sleep(0.001)
[help] 	return i
[help] 
[help] go4_return = runAsWorker(func=go4,args=(10,),worker_name="go2 worker",worker_on_abort=lambda: print("horay"))
[help] # or
[help] go4_return = runAsWorker(go4,10)
[help] # or
[help] go4_return = runAsWorker(go4,n=10)
[help] # or
[help] go4_return = runAsWorker(go4,n=10,worker_name="go2 worker",worker_on_abort=lambda: print("horay"))
[help] # or
[help] go4_return = runAsWorker(func=go4,args=(10,))
[help] 
[help] 
[help] 
[help] 
[help] =========================================================
[help] ---------------------- ADVANCED USE ---------------------
[help] =========================================================
[help] 
[help] # example using undefined worker function
[help] 
[help] go4_return = runAsWorker(func=go4,args=(10,))
[help] 
[help] # example using defined function with worker decorator '@worker'
[help] 
[help] go2_return = go2(100)
[help] 
[help] 
[help] 
[help] HOW TO GET THE RETURN?
[help] ##########################################################
[help] 
[help] go4_return = go4_return.ret
[help] 
[help] go2_return = go2_return.ret
[help] 
[help] 
[help] 
[help] HOW TO CHECK THE THREAD IS STILL RUNNING?
[help] ########################################################
[help] 
[help] go4_is_alive = go4_return.is_alive
[help] 
[help] go2_is_alive = go2_return.is_alive
[help] 
[help] 
[help] 
[help] HOW TO ABORT RUNNING WORKER?
[help] ########################################################
[help] 
[help] go4_return.abort()
[help] 
[help] go2_return.abort()
[help] 
[help] # or
[help] 
[help] # import this in your scripts
[help] from worker import abort_all_worker
[help] 
[help] 
[help] 
[help] 
[help] 
[help] 
[help] HOW TO ABORT ALL RUNNING WORKER?
[help] ########################################################
[help] 
[help] # import this in your scripts
[help] from worker import abort_all_worker
[help] 
[help] 
[help] # run this
[help] abort_all_worker()
[help] 
[help] 
[help] 
[help] 
######## HELP ######## HELP ######## HELP ######## HELP ######## HELP ######## HELP ########

"""