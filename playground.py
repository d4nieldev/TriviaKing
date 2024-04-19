import threading
import time
import sys
import select
# Event object to signal the termination of the waiting thread
terminate_event = threading.Event()
def wait_for_input():
    while not terminate_event.is_set():
        # Use select to check if there is input available without blocking
        input_ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if input_ready:
            try:
                # Read user input
                user_input = sys.stdin.readline().rstrip()
                print("got " + user_input)
            except (KeyboardInterrupt, EOFError):
                # Handle keyboard interrupts and end-of-file errors
                terminate_event.set()
                break
def monitor_condition():
    # Simulate some condition to trigger termination
    time.sleep(5)  # Wait for 5 seconds
    terminate_event.set()  # Signal termination after 5 seconds
# Create and start the threads
input_thread = threading.Thread(target=wait_for_input)
monitor_thread = threading.Thread(target=monitor_condition)
input_thread.start()
monitor_thread.start()
# Wait for both threads to complete
input_thread.join()
monitor_thread.join()
print("All threads have completed.")