from typing import List, Dict
from abc import ABC, abstractmethod
from threading import Lock
from datetime import datetime, timedelta
from enum import Enum, auto


def singleton(cls):
    instances = {}
    lock = Lock()

    def get_instance(*args, **kwargs):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id


class SeatStatus(Enum):
    AVAILABLE = auto()
    LOCKED = auto()
    BOOKED = auto()


class SeatType(Enum):
    SILVER = 150
    GOLD = 250
    PLATINUM = 400


class Seat:
    def __init__(self, seat_id: str, seat_type: SeatType):
        self.seat_id = seat_id
        self.seat_type = seat_type
        self.price = seat_type.value


class Movie:
    def __init__(self, movie_id: str, title: str, duration: int):
        self.movie_id = movie_id
        self.title = title
        self.duration = duration  # in minutes


class Theatre:
    def __init__(self, theatre_id: str, name: str):
        self.theatre_id = theatre_id
        self.name = name
        self.screens: Dict[str, 'Screen'] = {}

    def add_screen(self, screen: 'Screen'):
        self.screens[screen.screen_id] = screen


class Screen:
    def __init__(self, screen_id: str, seats: List[Seat]):
        self.screen_id = screen_id
        self.seats = seats


class Show:
    def __init__(self, show_id: str, movie: Movie, screen: Screen, start_time: datetime):
        self.show_id = show_id
        self.movie = movie
        self.screen = screen
        self.start_time = start_time
        self.seats = screen.seats


class SeatLock:
    def __init__(self, seat: Seat, show: Show, timeout: int, user: User):
        self.seat = seat
        self.show = show
        self.user = user
        self.lock_time = datetime.now()
        self.timeout = timeout

    def is_expired(self) -> bool:
        return datetime.now() > self.lock_time + timedelta(seconds=self.timeout)


class ISeatLockProvider(ABC):
    @abstractmethod
    def lock_seat(self, seat: Seat, show: Show, user: User): pass
    @abstractmethod
    def is_locked(self, seat: Seat, show: Show) -> bool: pass
    @abstractmethod
    def validate_locks(self, user: User, show: Show, seats: List[Seat]) -> bool: pass


@singleton
class SeatLockProvider(ISeatLockProvider):
    def __init__(self, lock_timeout: int = 60):
        self.lock_timeout = lock_timeout
        self.locks: Dict[str, SeatLock] = {}
        self.lock = Lock()

    def _generate_key(self, show: Show, seat: Seat) -> str:
        return f"{show.show_id}_{seat.seat_id}"

    def lock_seat(self, seat: Seat, show: Show, user: User):
        with self.lock:
            key = self._generate_key(show, seat)
            if key in self.locks and not self.locks[key].is_expired():
                raise Exception(f"Seat {seat.seat_id} is already locked.")
            self.locks[key] = SeatLock(seat, show, self.lock_timeout, user)

    def is_locked(self, seat: Seat, show: Show) -> bool:
        key = self._generate_key(show, seat)
        return key in self.locks and not self.locks[key].is_expired()

    def validate_locks(self, user: User, show: Show, seats: List[Seat]) -> bool:
        for seat in seats:
            key = self._generate_key(show, seat)
            if key not in self.locks or self.locks[key].user.user_id != user.user_id or self.locks[key].is_expired():
                return False
        return True


@singleton
class LockManager:
    def __init__(self):
        self.locks: Dict[str, Lock] = {}  # key = show_id_seat_id

    def get_lock(self, show_id: str, seat_id: str) -> Lock:
        key = f"{show_id}_{seat_id}"
        if key not in self.locks:
            self.locks[key] = Lock()
        return self.locks[key]  # return seat-specific lock


@singleton
class IPaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float, user: User):
        pass


class CreditCardPayment(IPaymentStrategy):
    def pay(self, amount: float, user: User):
        print(f"Processing credit card payment of ₹{amount} for user {user.user_id}")


class UpiPayment(IPaymentStrategy):
    def pay(self, amount: float, user: User):
        print(f"Processing UPI payment of ₹{amount} for user {user.user_id}")


class BookingService:
    def __init__(self, seat_lock_provider: ISeatLockProvider, payment_strategy: IPaymentStrategy):
        self.seat_lock_provider = seat_lock_provider
        self.payment_strategy = payment_strategy
        self.bookings: Dict[str, List[str]] = {}  # show_id -> list of booked seat ids
        self.lock_manager = LockManager()

    def book_seats(self, user: User, show: Show, seats: List[Seat]):
        acquired_locks = []
        try:
            for seat in seats:
                lock = self.lock_manager.get_lock(show.show_id, seat.seat_id)
                if not lock.acquire(blocking=False):
                    raise Exception(f"Could not acquire lock for seat {seat.seat_id}")
                acquired_locks.append(lock)

            if not self.seat_lock_provider.validate_locks(user, show, seats):
                raise Exception("All seats must be locked by the same user before booking.")

            for seat in seats:
                if seat.seat_id in self.bookings.get(show.show_id, []):
                    raise Exception(f"Seat {seat.seat_id} is already booked.")

            total_amount = sum(seat.price for seat in seats)
            self.payment_strategy.pay(total_amount, user)
            self.bookings.setdefault(show.show_id, []).extend([seat.seat_id for seat in seats])
        finally:
            for lock in acquired_locks:
                lock.release()

    def get_booked_seats(self, show: Show) -> List[str]:
        return self.bookings.get(show.show_id, [])
