import threading
import time
from collections import deque
from abc import ABC, abstractmethod

# =====================
# Strategy Interface
# =====================
class ISchedulingStrategy(ABC):
    @abstractmethod
    def add_task(self, task):
        pass

    @abstractmethod
    def get_task(self):
        pass

# =====================
# FIFO Strategy
# =====================
class FIFOStrategy(ISchedulingStrategy):
    def __init__(self):
        self.tasks = deque()
        self.lock = threading.Lock()

    def add_task(self, task):
        with self.lock:
            self.tasks.append(task)

    def get_task(self):
        with self.lock:
            if self.tasks:
                return self.tasks.popleft()
            return None

# =====================
# Task Scheduler
# =====================
class TaskScheduler:
    def __init__(self, strategy: ISchedulingStrategy):
        self.strategy = strategy

    def submit(self, task):
        self.strategy.add_task(task)

    def fetch(self):
        return self.strategy.get_task()

# =====================
# Worker Thread
# =====================
class Worker(threading.Thread):
    def __init__(self, scheduler, shutdown_flag):
        super().__init__()
        self.scheduler = scheduler
        self.shutdown_flag = shutdown_flag

    def run(self):
        while not self.shutdown_flag.is_set():
            task = self.scheduler.fetch()
            if task:
                task()
            else:
                time.sleep(0.1)

# =====================
# ThreadPool (LLD abstraction)
# =====================
class ThreadPool:
    def __init__(self, num_threads, strategy: ISchedulingStrategy):
        self.scheduler = TaskScheduler(strategy)
        self.shutdown_flag = threading.Event()
        self.workers = [Worker(self.scheduler, self.shutdown_flag) for _ in range(num_threads)]
        for worker in self.workers:
            worker.start()

    def submit_task(self, task):
        self.scheduler.submit(task)

    def shutdown(self):
        self.shutdown_flag.set()
        for worker in self.workers:
            worker.join()

# =====================
# Example Task
# =====================
class Task:
    def __init__(self, name):
        self.name = name

    def __call__(self):
        print(f"[{threading.current_thread().name}] Executing: {self.name}")
        time.sleep(1)
        print(f"[{threading.current_thread().name}] Completed: {self.name}")

# =====================
# Main Execution
# =====================
if __name__ == "__main__":
    pool = ThreadPool(3, FIFOStrategy())

    for i in range(10):
        pool.submit_task(Task(f"Task-{i+1}"))

    time.sleep(5)
    pool.shutdown()

    print("All tasks completed. ThreadPool shut down.")
