
# Enums for Vehicle, Reservation and Statuses
from enum import Enum

class VehicleType(Enum):
    ECONOMY = "Economy"
    LUXURY = "Luxury"
    SUV = "SUV"
    BIKE = "Bike"
    AUTO = "Auto"

class VehicleStatus(Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    RENTED = "Rented"
    MAINTENANCE = "Maintenance"
    OUT_OF_SERVICE = "OutOfService"

class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

# Location entity for stores
class Location:
    def __init__(self, address, city, state, zip_code):
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code

# Base Vehicle class with dynamic rental fee logic
class Vehicle:
    def __init__(self, reg_number, model, vtype: VehicleType, base_rent):
        self.reg_number = reg_number
        self.model = model
        self.type = vtype
        self.status = VehicleStatus.AVAILABLE
        self.base_rent = base_rent

    def calculate_fee(self, days):
        return self.base_rent * days  # overridden in subclasses

# Different vehicle types with their own fee calculation logic
class EconomyVehicle(Vehicle):
    def calculate_fee(self, days):
        return self.base_rent * days

class LuxuryVehicle(Vehicle):
    def calculate_fee(self, days):
        return self.base_rent * days * 2.5 + 50  # premium

class SUVVehicle(Vehicle):
    def calculate_fee(self, days):
        return self.base_rent * days * 1.5

# Vehicle factory to create various vehicles
class VehicleFactory:
    @staticmethod
    def create_vehicle(vtype, reg_number, model, base_rent):
        if vtype == VehicleType.ECONOMY:
            return EconomyVehicle(reg_number, model, vtype, base_rent)
        elif vtype == VehicleType.LUXURY:
            return LuxuryVehicle(reg_number, model, vtype, base_rent)
        elif vtype == VehicleType.SUV:
            return SUVVehicle(reg_number, model, vtype, base_rent)
        else:
            return Vehicle(reg_number, model, vtype, base_rent)

# Payment strategy pattern
class PaymentStrategy:
    def process_payment(self, amount):
        raise NotImplementedError

class CreditCardPayment(PaymentStrategy):
    def process_payment(self, amount):
        print(f"Paid ${amount} via Credit Card")

class CashPayment(PaymentStrategy):
    def process_payment(self, amount):
        print(f"Paid ${amount} in Cash")

# Reservation object holding booking details
class Reservation:
    def __init__(self, id, user, vehicle, pickup_store, return_store, start_date, end_date):
        self.id = id
        self.user = user
        self.vehicle = vehicle
        self.pickup_store = pickup_store
        self.return_store = return_store
        self.start_date = start_date
        self.end_date = end_date
        self.status = ReservationStatus.PENDING

        days = (end_date - start_date).days + 1
        self.total = vehicle.calculate_fee(days)

    def confirm(self):
        if self.status == ReservationStatus.PENDING:
            self.status = ReservationStatus.CONFIRMED
            self.vehicle.status = VehicleStatus.RESERVED

    def start_rental(self):
        if self.status == ReservationStatus.CONFIRMED:
            self.status = ReservationStatus.IN_PROGRESS
            self.vehicle.status = VehicleStatus.RENTED

    def complete_rental(self):
        if self.status == ReservationStatus.IN_PROGRESS:
            self.status = ReservationStatus.COMPLETED
            self.vehicle.status = VehicleStatus.AVAILABLE

    def cancel(self):
        if self.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            self.status = ReservationStatus.CANCELED
            self.vehicle.status = VehicleStatus.AVAILABLE

# User entity
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        self.reservations = []

    def add_reservation(self, res):
        self.reservations.append(res)

# Store containing vehicles
class RentalStore:
    def __init__(self, id, name, location):
        self.id = id
        self.name = name
        self.location = location
        self.vehicles = {}  # key: reg_number

    def add_vehicle(self, vehicle):
        self.vehicles[vehicle.reg_number] = vehicle

    def get_vehicle(self, reg):
        return self.vehicles.get(reg)

    def get_available_vehicles(self):
        return [v for v in self.vehicles.values() if v.status == VehicleStatus.AVAILABLE]

# Handles reservations system-wide
class ReservationManager:
    def __init__(self):
        self.reservations = {}
        self.counter = 1

    def create(self, user, vehicle, pickup, drop, start, end):
        res = Reservation(self.counter, user, vehicle, pickup, drop, start, end)
        self.reservations[self.counter] = res
        user.add_reservation(res)
        self.counter += 1
        return res

# Singleton Rental System to orchestrate all
class RentalSystem:
    _instance = None

    def __init__(self):
        self.stores = []
        self.users = {}
        self.reservations = ReservationManager()
        self.vehicle_factory = VehicleFactory()
        self.counter = 1

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RentalSystem()
        return cls._instance

    def add_store(self, store):
        self.stores.append(store)

    def register_user(self, name, email):
        user = User(self.counter, name, email)
        self.users[self.counter] = user
        self.counter += 1
        return user

    def create_reservation(self, user_id, reg_number, pickup_id, return_id, start, end):
        user = self.users.get(user_id)
        pickup = next((s for s in self.stores if s.id == pickup_id), None)
        drop = next((s for s in self.stores if s.id == return_id), None)
        vehicle = pickup.get_vehicle(reg_number) if pickup else None

        if user and vehicle:
            return self.reservations.create(user, vehicle, pickup, drop, start, end)

    def process_payment(self, reservation, strategy):
        strategy.process_payment(reservation.total)
        reservation.confirm()

    def start_rental(self, reservation):
        reservation.start_rental()

    def complete_rental(self, reservation):
        reservation.complete_rental()