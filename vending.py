
# Python implementation of the Vending Machine system
# Includes State pattern to manage machine behavior transitions

from enum import Enum, auto
from typing import List, Optional


# ------------------------
# ENUMS & MODELS
# ------------------------
class Coin(Enum):
    PENNY = 1
    NICKEL = 5
    DIME = 10
    QUARTER = 25


class ItemType(Enum):
    COKE = auto()
    PEPSI = auto()
    JUICE = auto()
    SODA = auto()


class Item:
    def __init__(self, item_type: ItemType, price: int):
        self.type = item_type
        self.price = price


class ItemShelf:
    def __init__(self, code: int):
        self.code = code
        self.item: Optional[Item] = None
        self.sold_out: bool = True


class Inventory:
    def __init__(self, item_count: int):
        self.inventory = [ItemShelf(101 + i) for i in range(item_count)]

    def add_item(self, item: Item, code: int):
        for shelf in self.inventory:
            if shelf.code == code:
                if shelf.sold_out:
                    shelf.item = item
                    shelf.sold_out = False
                    return
                raise Exception("Item already present")

    def get_item(self, code: int) -> Item:
        for shelf in self.inventory:
            if shelf.code == code:
                if shelf.sold_out:
                    raise Exception("Item sold out")
                return shelf.item
        raise Exception("Invalid Code")

    def mark_sold_out(self, code: int):
        for shelf in self.inventory:
            if shelf.code == code:
                shelf.sold_out = True


# ------------------------
# VENDING MACHINE CORE
# ------------------------
class VendingMachine:
    def __init__(self):
        self.state: 'State' = IdleState(self)
        self.inventory = Inventory(10)
        self.coins: List[Coin] = []


# ------------------------
# STATE INTERFACE
# ------------------------
class State:
    def click_insert_coin(self, machine: VendingMachine):
        raise NotImplementedError()

    def click_product_selection(self, machine: VendingMachine):
        raise NotImplementedError()

    def insert_coin(self, machine: VendingMachine, coin: Coin):
        raise NotImplementedError()

    def choose_product(self, machine: VendingMachine, code: int):
        raise NotImplementedError()

    def get_change(self, change: int):
        raise NotImplementedError()

    def dispense(self, machine: VendingMachine, code: int):
        raise NotImplementedError()

    def refund(self, machine: VendingMachine):
        raise NotImplementedError()

    def update_inventory(self, machine: VendingMachine, item: Item, code: int):
        raise NotImplementedError()


# ------------------------
# STATE IMPLEMENTATIONS
# ------------------------
class IdleState(State):
    def __init__(self, machine: VendingMachine):
        print("VendingMachine in IDLE state")
        machine.coins = []
        machine.state = self

    def click_insert_coin(self, machine: VendingMachine):
        machine.state = HasMoneyState()

    def update_inventory(self, machine: VendingMachine, item: Item, code: int):
        machine.inventory.add_item(item, code)


class HasMoneyState(State):
    def __init__(self):
        print("VendingMachine in HAS_MONEY state")

    def click_product_selection(self, machine: VendingMachine):
        machine.state = SelectionState()

    def insert_coin(self, machine: VendingMachine, coin: Coin):
        print(f"Accepted coin: {coin.name}")
        machine.coins.append(coin)

    def refund(self, machine: VendingMachine):
        print("Refunding full amount")
        machine.state = IdleState(machine)
        return machine.coins


class SelectionState(State):
    def __init__(self):
        print("VendingMachine in SELECTION state")

    def choose_product(self, machine: VendingMachine, code: int):
        item = machine.inventory.get_item(code)
        total_paid = sum(coin.value for coin in machine.coins)

        if total_paid < item.price:
            print(f"Insufficient funds. Paid: {total_paid}, Required: {item.price}")
            self.refund(machine)
            raise Exception("Insufficient payment")

        if total_paid > item.price:
            self.get_change(total_paid - item.price)

        machine.state = DispenseState(machine, code)

    def get_change(self, change: int):
        print(f"Returned change: {change}")
        return change

    def refund(self, machine: VendingMachine):
        print("Refunding full amount from SELECTION")
        machine.state = IdleState(machine)
        return machine.coins


class DispenseState(State):
    def __init__(self, machine: VendingMachine, code: int):
        print("VendingMachine in DISPENSE state")
        self.dispense(machine, code)

    def dispense(self, machine: VendingMachine, code: int):
        item = machine.inventory.get_item(code)
        print(f"Dispensing: {item.type.name}")
        machine.inventory.mark_sold_out(code)
        machine.state = IdleState(machine)


# ------------------------
# TEST SIMULATION
# ------------------------
if __name__ == '__main__':
    machine = VendingMachine()

    # Fill inventory
    for i in range(10):
        if i < 3:
            machine.state.update_inventory(machine, Item(ItemType.COKE, 12), 101 + i)
        elif i < 5:
            machine.state.update_inventory(machine, Item(ItemType.PEPSI, 9), 101 + i)
        elif i < 7:
            machine.state.update_inventory(machine, Item(ItemType.JUICE, 13), 101 + i)
        else:
            machine.state.update_inventory(machine, Item(ItemType.SODA, 7), 101 + i)

    # User interaction simulation
    machine.state.click_insert_coin(machine)  # Go to HasMoney
    machine.state.insert_coin(machine, Coin.NICKEL)
    machine.state.insert_coin(machine, Coin.QUARTER)

    machine.state.click_product_selection(machine)  # Go to Selection
    machine.state.choose_product(machine, 102)  # Select product
