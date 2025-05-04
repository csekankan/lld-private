
# Low-Level Design for a Vending Machine System in Python
# -------------------------------------------------------
# This design includes:
# - State pattern to manage machine states
# - Strategy pattern for extensible payment handling
# - Core classes: Item, ItemShelf, Inventory
# - Coin handling
# - User interaction simulated in main

from enum import Enum
from typing import List

# -------------------------------------------------------
# Enum for Product Types
class ItemType(Enum):
    COKE = "Coke"
    PEPSI = "Pepsi"
    JUICE = "Juice"
    SODA = "Soda"


# -------------------------------------------------------
# Product Item
class Item:
    def __init__(self, item_type: ItemType, price: int):
        self.type = item_type
        self.price = price


# -------------------------------------------------------
# Each shelf holds multiple items
class ItemShelf:
    def __init__(self, code: int):
        self.code = code
        self.items: List[Item] = []
        self.is_sold_out = False

    def add_item(self, item: Item):
        self.items.append(item)
        self.is_sold_out = False

    def remove_item(self) -> Item:
        if not self.items:
            self.is_sold_out = True
            raise Exception("Item out of stock")
        item = self.items.pop(0)
        if not self.items:
            self.is_sold_out = True
        return item


# -------------------------------------------------------
# Enum for supported Coin Denominations
class Coin(Enum):
    ONE = 1
    TWO = 2
    FIVE = 5
    TEN = 10


# -------------------------------------------------------
# Inventory system with shelf codes
class Inventory:
    def __init__(self, size: int):
        self.shelves: List[ItemShelf] = [ItemShelf(100 + i) for i in range(size)]

    def add_item(self, code: int, item: Item):
        for shelf in self.shelves:
            if shelf.code == code:
                shelf.add_item(item)
                return
        raise Exception("Invalid shelf code")

    def get_item(self, code: int) -> Item:
        for shelf in self.shelves:
            if shelf.code == code:
                return shelf.remove_item()
        raise Exception("Invalid shelf code")

    def has_items(self) -> bool:
        return any(len(shelf.items) > 0 for shelf in self.shelves)

    def display(self):
        for shelf in self.shelves:
            print(f"Shelf {shelf.code} | Items: {len(shelf.items)} | SoldOut: {shelf.is_sold_out}")


# -------------------------------------------------------
# Vending Machine Context and State Management
class VendingMachine:
    def __init__(self):
        self.state = "IDLE"
        self.inventory = Inventory(10)
        self.inserted_coins: List[Coin] = []
        self.selected_code: int = None

    def insert_coin(self, coin: Coin):
        if self.state not in ["IDLE", "HAS_MONEY"]:
            raise Exception("Can't insert coins in current state")
        print(f"Coin inserted: {coin.name} ({coin.value})")
        self.inserted_coins.append(coin)
        self.state = "HAS_MONEY"

    def select_product(self, code: int):
        if self.state != "HAS_MONEY":
            raise Exception("Insert coins before selecting item")
        self.selected_code = code
        total = sum(c.value for c in self.inserted_coins)
        try:
            item = self.inventory.get_item(code)
            if total < item.price:
                raise Exception(f"Insufficient funds. Price: {item.price}, Paid: {total}")
            change = total - item.price
            print(f"Dispensing {item.type.value}. Change returned: {change}")
            self.reset()
        except Exception as e:
            print(f"Error: {str(e)}")
            self.reset()

    def reset(self):
        self.state = "IDLE"
        self.inserted_coins.clear()
        self.selected_code = None

    def load_items(self):
        # Load demo items into shelves
        for i in range(10):
            item_type = [ItemType.COKE, ItemType.PEPSI, ItemType.JUICE, ItemType.SODA][i % 4]
            price = 10 + (i % 3) * 5
            for _ in range(3):
                self.inventory.add_item(100 + i, Item(item_type, price))

    def display_inventory(self):
        self.inventory.display()


# -------------------------------------------------------
# Main method for simulating the vending machine
if __name__ == "__main__":
    vm = VendingMachine()
    vm.load_items()
    vm.display_inventory()
    print("\nUser inserts coins...")
    vm.insert_coin(Coin.TEN)
    vm.insert_coin(Coin.FIVE)
    print("\nUser selects product from shelf 101...")
    vm.select_product(101)
    print("\nFinal Inventory:")
    vm.display_inventory()
