import multiprocessing
import sys

# This background thread is responsible for recording information from the
# transmission layer and printing it to both console and log.txt.
def bg_log(q):
    with open("log.txt", "a") as f:
        while True:
            item = q.get()
            if item is None:
                continue
            else:
                print(item)
                sys.stdout.flush()
                f.write(item + "\n")
                f.flush()

logevent_queue = multiprocessing.Queue()
logger_process = multiprocessing.Process(target=bg_log, args=(logevent_queue,))
print("Starting background logging thread.")
logger_process.start()

def burrow_log(string_to_log, number_of_spaces):
    logevent_queue.put(" " * number_of_spaces + string_to_log)
