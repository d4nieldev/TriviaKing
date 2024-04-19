import threading

t1 = threading.Thread(target=lambda: print("Hello from thread 1"))
t1.start()
t1.join()
t1.start()