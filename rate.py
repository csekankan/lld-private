# Extended Python Rate Limiter with Token Bucket, Fixed Window, and Sliding Window Strategies
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Callable, Optional
from enum import Enum
from collections import defaultdict, deque


class IRateLimiter:
    def give_access(self, key: Optional[str] = None) -> bool:
        raise NotImplementedError

    def update_configuration(self, config: Dict):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError


class TokenBucketStrategy(IRateLimiter):
    class Bucket:
        def __init__(self, capacity: int, refresh_rate: int):
            self.capacity = capacity
            self.tokens = capacity
            self.refresh_rate = refresh_rate
            self.lock = threading.Lock()
            self.last_refill_time = time.time()

        def try_consume(self) -> bool:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill_time
                tokens_to_add = int(elapsed * self.refresh_rate)
                if tokens_to_add > 0:
                    self.tokens = min(self.capacity, self.tokens + tokens_to_add)
                    self.last_refill_time = now
                if self.tokens > 0:
                    self.tokens -= 1
                    return True
                return False

        def refill(self):
            with self.lock:
                self.tokens = min(self.capacity, self.tokens + self.refresh_rate)

    def __init__(self, capacity: int, refresh_rate: int):
        self.capacity = capacity
        self.refresh_rate = refresh_rate
        self.global_bucket = self.Bucket(capacity, refresh_rate)
        self.user_buckets: Dict[str, TokenBucketStrategy.Bucket] = {}
        self.lock = threading.Lock()
        self.running = True
        self.refill_thread = threading.Thread(target=self._refill_task, daemon=True)
        self.refill_thread.start()

    def _refill_task(self):
        while self.running:
            time.sleep(1)
            self.global_bucket.refill()
            with self.lock:
                for bucket in self.user_buckets.values():
                    bucket.refill()

    def give_access(self, key: Optional[str] = None) -> bool:
        if key:
            with self.lock:
                if key not in self.user_buckets:
                    self.user_buckets[key] = self.Bucket(self.capacity, self.refresh_rate)
                bucket = self.user_buckets[key]
        else:
            bucket = self.global_bucket
        return bucket.try_consume()

    def update_configuration(self, config: Dict):
        if 'refresh_rate' in config:
            self.refresh_rate = config['refresh_rate']

    def shutdown(self):
        self.running = False
        self.refill_thread.join()


class FixedWindowStrategy(IRateLimiter):
    def __init__(self, window_size_sec: int, max_requests: int):
        self.window_size_sec = window_size_sec
        self.max_requests = max_requests
        self.lock = threading.Lock()
        self.window_start = time.time()
        self.counter = 0

    def give_access(self, key: Optional[str] = None) -> bool:
        with self.lock:
            now = time.time()
            if now - self.window_start >= self.window_size_sec:
                self.window_start = now
                self.counter = 0
            if self.counter < self.max_requests:
                self.counter += 1
                return True
            return False

    def update_configuration(self, config: Dict):
        if 'max_requests' in config:
            self.max_requests = config['max_requests']

    def shutdown(self):
        pass


class SlidingWindowStrategy(IRateLimiter):
    def __init__(self, window_size_sec: int, max_requests: int):
        self.window_size_sec = window_size_sec
        self.max_requests = max_requests
        self.lock = threading.Lock()
        self.timestamps = defaultdict(deque)

    def give_access(self, key: Optional[str] = None) -> bool:
        key = key or 'global'
        now = time.time()
        with self.lock:
            q = self.timestamps[key]
            while q and now - q[0] > self.window_size_sec:
                q.popleft()
            if len(q) < self.max_requests:
                q.append(now)
                return True
            return False

    def update_configuration(self, config: Dict):
        if 'max_requests' in config:
            self.max_requests = config['max_requests']

    def shutdown(self):
        pass


class RateLimiterType(Enum):
    TOKEN_BUCKET = 1
    FIXED_WINDOW = 2
    SLIDING_WINDOW = 3


class RateLimiterFactory:
    limiter_factories: Dict[RateLimiterType, Callable[[Dict], IRateLimiter]] = {
        RateLimiterType.TOKEN_BUCKET: lambda config: TokenBucketStrategy(
            config.get('capacity', 10),
            config.get('refresh_rate', 1)
        ),
        RateLimiterType.FIXED_WINDOW: lambda config: FixedWindowStrategy(
            config.get('window_size', 1),
            config.get('max_requests', 5)
        ),
        RateLimiterType.SLIDING_WINDOW: lambda config: SlidingWindowStrategy(
            config.get('window_size', 1),
            config.get('max_requests', 5)
        ),
    }

    @classmethod
    def create_limiter(cls, limiter_type: RateLimiterType, config: Dict) -> IRateLimiter:
        if limiter_type not in cls.limiter_factories:
            raise ValueError(f"Unsupported limiter type: {limiter_type}")
        return cls.limiter_factories[limiter_type](config)


class RateLimiterController:
    def __init__(self, limiter_type: RateLimiterType, config: Dict):
        self.limiter = RateLimiterFactory.create_limiter(limiter_type, config)
        self.executor = ThreadPoolExecutor(max_workers=10)

    def process_request(self, key: Optional[str] = None):
        def task():
            allowed = self.limiter.give_access(key)
            print(f"Request with key [{key}]: {'✅ Allowed' if allowed else '❌ Blocked'}")
            return allowed
        return self.executor.submit(task)

    def update_configuration(self, config: Dict):
        self.limiter.update_configuration(config)

    def shutdown(self):
        self.limiter.shutdown()
        self.executor.shutdown()


def send_burst_requests(controller: RateLimiterController, count: int, key: Optional[str]):
    futures = [controller.process_request(key) for _ in range(count)]
    allowed = sum(f.result() for f in as_completed(futures))
    print(f"Results: {allowed} allowed, {count - allowed} blocked (total: {count})")


def main():
    configs = {
        RateLimiterType.TOKEN_BUCKET: {'capacity': 5, 'refresh_rate': 1},
        RateLimiterType.FIXED_WINDOW: {'window_size': 1, 'max_requests': 5},
        RateLimiterType.SLIDING_WINDOW: {'window_size': 1, 'max_requests': 5},
    }

    for limiter_type in RateLimiterType:
        print(f"\n=== Testing {limiter_type.name} Rate Limiter ===")
        controller = RateLimiterController(limiter_type, configs[limiter_type])
        send_burst_requests(controller, 10, None)
        time.sleep(2)
        controller.shutdown()


if __name__ == '__main__':
    main()
