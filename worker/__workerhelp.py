help_msg = """
@worker will define a function as a thread object once it run

---------------------------------------------------
SIMPLE USE (example)
###################################################
from worker import worker

@worker #-> this is the threading decorator
def go():
for i in range(10):
    print('AAAA', i)
    time.sleep(1)
print('done')

@worker('worker ganteng') #-> this is the threading decorator with process name
def go1():
for i in range(10):
    print('AAAA', i)
    time.sleep(1)
print('done')

# on_abort -> when the worker is aborted, it will raise on_abort
# on_abort -> workername is required when using ob_abort params
@worker('worker cool',on_abort=lambda: print("its aborted!")) 
def coba():
    a = go()
    #-> wait() will block the next line till go() is done
    a.wait()
    print('HAHAHAHAHH')

-----------------------------------------------------
AVAILABLE MODEL
#####################################################
set worker decorator only have 3 model

++++++ model 1 ++++++
@worker
def go1():
    i = 0
    while 1:
        i+=1
        time.sleep(0.005)
    return i

++++++ model 2 ++++++
@worker("gogogo")
def go2(n=1):
    i = 0
    while 1:
        i+=n
        time.sleep(0.005)
    return i

++++++ model 3 ++++++
@worker("gogagaaaa",on_abort=lambda: print("HAHAHAHAH"))
def go3():
    i = 0
    while 1:
        i+=1
        time.sleep(0.005)
    return i


HOW TO RUN DEFINED WORKER?
#####################################

go2(n=100)

# or

go2(100)

# or

a = go1()

# or

b = go2(300)




AVAILABLE "run as worker" MODEL
##########################################################
runAsWorker only works these ways


def go4(n=1):
    i = 0
    while i < 1e3/2:
        i += n
        print(i)
        time.sleep(0.001)
    return i

go4_return = runAsWorker(func=go4,args=(10,),worker_name="go2 worker",worker_on_abort=lambda: print("horay"))

# or

go4_return = runAsWorker(go4,10)

# or

go4_return = runAsWorker(go4,n=10)

# or

go4_return = runAsWorker(go4,n=10,worker_name="go2 worker",worker_on_abort=lambda: print("horay"))

# or

go4_return = runAsWorker(func=go4,args=(10,))




=========================================================
---------------------- ADVANCED USE ---------------------
=========================================================

# example using undefined worker function

go4_return = runAsWorker(func=go4,args=(10,))

# example using defined function with worker decorator '@worker'

go2_return = go2(100)



HOW TO GET THE RETURN?
##########################################################

go4_return = go4_return.ret

go2_return = go2_return.ret



HOW TO CHECK THE THREAD IS STILL RUNNING?
########################################################

go4_is_alive = go4_return.is_alive

go2_is_alive = go2_return.is_alive



HOW TO ABORT RUNNING WORKER?
########################################################

go4_return.abort()

go2_return.abort()

# or

# import this in your scripts
from worker import abort_all_worker






HOW TO ABORT ALL RUNNING WORKER?
########################################################

# import this in your scripts
from worker import abort_all_worker


# run this
abort_all_worker()
"""