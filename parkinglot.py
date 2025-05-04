# Parking Lot System - Low Level Design in Python
# ----------------------------------------------
# Entities:
# - Vehicle (Car, Bike, Other)
# - ParkingSpot (CarParkingSpot, BikeParkingSpot)
# - ParkingLot
# - Payment (Cash, CreditCard)
# - ParkingFeeStrategy (BasicHourly, Premium)
# - DurationType (Hours/Days)
# - VehicleFactory (to create vehicles with strategy)

from abc import ABC, abstractmethod
from enum import Enum

# Enum to represent duration type for parking
class DurationType(Enum):
    HOURS = 1
    DAYS = 2

# Strategy Pattern: Interface for parking fee calculation
class ParkingFeeStrategy(ABC):
    @abstractmethod
    def calculate_fee(self, vehicle_type: str, duration: int, duration_type: DurationType) -> float:
        pass

# Concrete implementation: Basic hourly rate strategy
class BasicHourlyRateStrategy(ParkingFeeStrategy):
    def calculate_fee(self, vehicle_type: str, duration: int, duration_type: DurationType) -> float:
        hourly_rates = {'car': 10, 'bike': 5, 'auto': 8}
        base = hourly_rates.get(vehicle_type.lower(), 15)
        if duration_type == DurationType.DAYS:
            duration *= 24
        return base * duration

# Concrete implementation: Premium rate strategy
class PremiumRateStrategy(ParkingFeeStrategy):
    def calculate_fee(self, vehicle_type: str, duration: int, duration_type: DurationType) -> float:
        premium_rates = {'car': 15, 'bike': 8, 'auto': 12}
        base = premium_rates.get(vehicle_type.lower(), 20)
        if duration_type == DurationType.DAYS:
            duration *= 24
        return base * duration

# Vehicle base class
class Vehicle:
    def __init__(self, license_plate: str, vehicle_type: str, fee_strategy: ParkingFeeStrategy):
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type
        self.fee_strategy = fee_strategy

    def calculate_fee(self, duration: int, duration_type: DurationType) -> float:
        return self.fee_strategy.calculate_fee(self.vehicle_type, duration, duration_type)

# Specific vehicle classes for type safety
class CarVehicle(Vehicle):
    def __init__(self, license_plate, fee_strategy):
        super().__init__(license_plate, "car", fee_strategy)

class BikeVehicle(Vehicle):
    def __init__(self, license_plate, fee_strategy):
        super().__init__(license_plate, "bike", fee_strategy)

class OtherVehicle(Vehicle):
    def __init__(self, license_plate, fee_strategy):
        super().__init__(license_plate, "other", fee_strategy)

# Factory to create vehicles with fee strategies
class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_type, license_plate, fee_strategy) -> Vehicle:
        if vehicle_type.lower() == "car":
            return CarVehicle(license_plate, fee_strategy)
        elif vehicle_type.lower() == "bike":
            return BikeVehicle(license_plate, fee_strategy)
        return OtherVehicle(license_plate, fee_strategy)

# Strategy Pattern: Interface for different payment methods
class PaymentStrategy(ABC):
    @abstractmethod
    def process_payment(self, amount: float):
        pass

# Concrete payment method: Cash
class CashPayment(PaymentStrategy):
    def process_payment(self, amount: float):
        print(f"Processing cash payment of ${amount:.2f}")

# Concrete payment method: Credit Card
class CreditCardPayment(PaymentStrategy):
    def process_payment(self, amount: float):
        print(f"Processing credit card payment of ${amount:.2f}")

# Payment context class
class Payment:
    def __init__(self, amount: float, strategy: PaymentStrategy):
        self.amount = amount
        self.strategy = strategy

    def pay(self):
        if self.amount > 0:
            self.strategy.process_payment(self.amount)
        else:
            print("Invalid payment amount.")

# Abstract ParkingSpot class
class ParkingSpot(ABC):
    def __init__(self, spot_number: int, spot_type: str):
        self.spot_number = spot_number
        self.spot_type = spot_type
        self.vehicle = None

    def is_occupied(self):
        return self.vehicle is not None

    def park_vehicle(self, vehicle: Vehicle):
        if self.is_occupied():
            raise Exception("Spot already occupied")
        if not self.can_park_vehicle(vehicle):
            raise Exception(f"{vehicle.vehicle_type} not suitable for this spot")
        self.vehicle = vehicle

    def vacate(self):
        if not self.is_occupied():
            raise Exception("Spot already vacant")
        self.vehicle = None

    @abstractmethod
    def can_park_vehicle(self, vehicle: Vehicle) -> bool:
        pass

# Specific implementation: Car spot
class CarParkingSpot(ParkingSpot):
    def __init__(self, spot_number):
        super().__init__(spot_number, "car")

    def can_park_vehicle(self, vehicle: Vehicle):
        return vehicle.vehicle_type.lower() == "car"

# Specific implementation: Bike spot
class BikeParkingSpot(ParkingSpot):
    def __init__(self, spot_number):
        super().__init__(spot_number, "bike")

    def can_park_vehicle(self, vehicle: Vehicle):
        return vehicle.vehicle_type.lower() == "bike"

# ParkingLot class - handles allocation and release
class ParkingLot:
    def __init__(self, spots):
        self.spots = spots

    def find_available_spot(self, vehicle_type: str):
        for spot in self.spots:
            if not spot.is_occupied() and spot.spot_type == vehicle_type.lower():
                return spot
        return None

    def park_vehicle(self, vehicle: Vehicle):
        spot = self.find_available_spot(vehicle.vehicle_type)
        if spot:
            spot.park_vehicle(vehicle)
            print(f"{vehicle.vehicle_type} parked at spot {spot.spot_number}")
            return spot
        print(f"No available spot for {vehicle.vehicle_type}")
        return None

    def vacate_spot(self, spot: ParkingSpot, vehicle: Vehicle):
        if spot and spot.is_occupied() and spot.vehicle == vehicle:
            spot.vacate()
            print(f"{vehicle.vehicle_type} vacated spot {spot.spot_number}")
        else:
            print("Invalid vacate operation")

# Main logic to demonstrate functionality
if __name__ == "__main__":
    basic_strategy = BasicHourlyRateStrategy()
    premium_strategy = PremiumRateStrategy()

    # Create parking spots for car and bike
    spots = [CarParkingSpot(1), CarParkingSpot(2), BikeParkingSpot(3), BikeParkingSpot(4)]
    lot = ParkingLot(spots)

    # Create vehicles
    car = VehicleFactory.create_vehicle("car", "ABC123", basic_strategy)
    bike = VehicleFactory.create_vehicle("bike", "BIKE456", premium_strategy)

    # Park the vehicles
    car_spot = lot.park_vehicle(car)
    bike_spot = lot.park_vehicle(bike)

    # Calculate fees
    car_fee = car.calculate_fee(2, DurationType.HOURS)
    bike_fee = bike.calculate_fee(3, DurationType.HOURS)

    # Process payments
    car_payment = Payment(car_fee, CreditCardPayment())
    bike_payment = Payment(bike_fee, CashPayment())

    car_payment.pay()
    bike_payment.pay()

    # Vacate spots
    lot.vacate_spot(car_spot, car)
    lot.vacate_spot(bike_spot, bike)
