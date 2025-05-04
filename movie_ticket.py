from typing import List, Dict
from threading import Lock
from datetime import datetime, timedelta


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


class Seat:
    def __init__(self, seat_id: str, seat_type: str):
        self.seat_id = seat_id
        self.seat_type = seat_type


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


@singleton
class SeatLockProvider:
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
class BookingService:
    def __init__(self, seat_lock_provider: SeatLockProvider):
        self.seat_lock_provider = seat_lock_provider
        self.bookings: Dict[str, List[str]] = {}  # show_id -> list of booked seat ids
        self.lock = Lock()

    def book_seats(self, user: User, show: Show, seats: List[Seat]):
        with self.lock:
            if not self.seat_lock_provider.validate_locks(user, show, seats):
                raise Exception("All seats must be locked by the same user before booking.")

            for seat in seats:
                if seat.seat_id in self.bookings.get(show.show_id, []):
                    raise Exception(f"Seat {seat.seat_id} is already booked.")

            self.bookings.setdefault(show.show_id, []).extend([seat.seat_id for seat in seats])

    def get_booked_seats(self, show: Show) -> List[str]:
        return self.bookings.get(show.show_id, [])


# Simulate full booking flow
def simulate_booking():
    user1 = User("user1")
    seats = [Seat("A1", "SILVER"), Seat("A2", "GOLD"), Seat("A3", "PLATINUM")]

    movie = Movie("m1", "Inception", 148)
    screen = Screen("screen1", seats)
    theatre = Theatre("theatre1", "Cineplex")
    theatre.add_screen(screen)

    show = Show("show1", movie, screen, datetime.now())

    seat_lock_provider = SeatLockProvider(lock_timeout=60)
    booking_service = BookingService(seat_lock_provider)

    try:
        seat_lock_provider.lock_seat(seats[0], show, user1)
        seat_lock_provider.lock_seat(seats[1], show, user1)
        booking_service.book_seats(user1, show, [seats[0], seats[1]])
        print("✅ Booking successful:", booking_service.get_booked_seats(show))
    except Exception as e:
        print("❌ Booking failed:", str(e))


if __name__ == "__main__":
    simulate_booking()
