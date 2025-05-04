
# Splitwise System (Python LLD Conversion)
# Phase 1: Core Models, Expense Logic, and Simulation with Comments

from enum import Enum
from typing import List, Dict


# -----------------------------
# ENUM: Expense Split Types
# -----------------------------
class ExpenseSplitType(Enum):
    EQUAL = "EQUAL"
    UNEQUAL = "UNEQUAL"
    PERCENTAGE = "PERCENTAGE"


# -----------------------------
# BALANCE Class
# -----------------------------
class Balance:
    def __init__(self):
        self.amount_owe: float = 0.0
        self.amount_get_back: float = 0.0


# -----------------------------
# USER Class
# -----------------------------
class User:
    def __init__(self, user_id: str, name: str):
        self.user_id = user_id
        self.name = name
        self.expense_sheet = UserExpenseBalanceSheet()


class UserExpenseBalanceSheet:
    def __init__(self):
        self.total_your_expense = 0.0
        self.total_payment = 0.0
        self.total_you_owe = 0.0
        self.total_you_get_back = 0.0
        self.user_vs_balance: Dict[str, Balance] = {}


# -----------------------------
# SPLIT Class
# -----------------------------
class Split:
    def __init__(self, user: User, amount_owe: float):
        self.user = user
        self.amount_owe = amount_owe


# -----------------------------
# EXPENSE Class
# -----------------------------
class Expense:
    def __init__(self, expense_id: str, amount: float, desc: str, paid_by: User,
                 split_type: ExpenseSplitType, splits: List[Split]):
        self.expense_id = expense_id
        self.amount = amount
        self.description = desc
        self.paid_by = paid_by
        self.split_type = split_type
        self.splits = splits


# -----------------------------
# STRATEGY INTERFACE
# -----------------------------
class ExpenseSplit:
    def validate(self, splits: List[Split], total_amount: float):
        raise NotImplementedError


# -----------------------------
# STRATEGY IMPLEMENTATIONS
# -----------------------------
class EqualExpenseSplit(ExpenseSplit):
    def validate(self, splits: List[Split], total_amount: float):
        per_head = total_amount / len(splits)
        for split in splits:
            if split.amount_owe != per_head:
                raise ValueError("Invalid equal split")


class UnequalExpenseSplit(ExpenseSplit):
    def validate(self, splits: List[Split], total_amount: float):
        total = sum(split.amount_owe for split in splits)
        if round(total, 2) != round(total_amount, 2):
            raise ValueError("Unequal split doesn't sum up to total")


class PercentageExpenseSplit(ExpenseSplit):
    def validate(self, splits: List[Split], total_amount: float):
        # For future use, assume pre-calculated values
        total = sum(split.amount_owe for split in splits)
        if round(total, 2) != round(total_amount, 2):
            raise ValueError("Percentage split doesn't sum up to total")


# -----------------------------
# SPLIT FACTORY
# -----------------------------
class SplitFactory:
    @staticmethod
    def get_strategy(split_type: ExpenseSplitType) -> ExpenseSplit:
        if split_type == ExpenseSplitType.EQUAL:
            return EqualExpenseSplit()
        elif split_type == ExpenseSplitType.UNEQUAL:
            return UnequalExpenseSplit()
        elif split_type == ExpenseSplitType.PERCENTAGE:
            return PercentageExpenseSplit()
        else:
            raise ValueError("Invalid split type")


# -----------------------------
# BALANCE SHEET CONTROLLER
# -----------------------------
class BalanceSheetController:
    def update(self, paid_by: User, splits: List[Split], amount: float):
        paid_by_sheet = paid_by.expense_sheet
        paid_by_sheet.total_payment += amount

        for split in splits:
            user = split.user
            owe_amount = split.amount_owe
            user_sheet = user.expense_sheet

            if user.user_id == paid_by.user_id:
                paid_by_sheet.total_your_expense += owe_amount
                continue

            paid_by_sheet.total_you_get_back += owe_amount
            if user.user_id not in paid_by_sheet.user_vs_balance:
                paid_by_sheet.user_vs_balance[user.user_id] = Balance()
            paid_by_sheet.user_vs_balance[user.user_id].amount_get_back += owe_amount

            user_sheet.total_you_owe += owe_amount
            user_sheet.total_your_expense += owe_amount
            if paid_by.user_id not in user_sheet.user_vs_balance:
                user_sheet.user_vs_balance[paid_by.user_id] = Balance()
            user_sheet.user_vs_balance[paid_by.user_id].amount_owe += owe_amount

    def show_user_balance(self, user: User):
        sheet = user.expense_sheet
        print(f"---- Balance Sheet for {user.name} ----")
        print(f"Total Expense: {sheet.total_your_expense}")
        print(f"Total You Owe: {sheet.total_you_owe}")
        print(f"Total You Get Back: {sheet.total_you_get_back}")
        print(f"Total Payment: {sheet.total_payment}")
        for uid, balance in sheet.user_vs_balance.items():
            print(f"User: {uid}, You Owe: {balance.amount_owe}, You Get Back: {balance.amount_get_back}")
        print("--------------------------------------")


# -----------------------------
# EXPENSE CONTROLLER
# -----------------------------
class ExpenseController:
    def __init__(self):
        self.balance_ctrl = BalanceSheetController()

    def create_expense(self, expense_id: str, desc: str, amount: float,
                       splits: List[Split], split_type: ExpenseSplitType, paid_by: User) -> Expense:
        strategy = SplitFactory.get_strategy(split_type)
        strategy.validate(splits, amount)
        expense = Expense(expense_id, amount, desc, paid_by, split_type, splits)
        self.balance_ctrl.update(paid_by, splits, amount)
        return expense


# -----------------------------
# USER CONTROLLER
# -----------------------------
class UserController:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def add_user(self, user: User):
        self.users[user.user_id] = user

    def get_user(self, user_id: str) -> User:
        return self.users[user_id]

    def get_all_users(self) -> List[User]:
        return list(self.users.values())


# -----------------------------
# SPLITWISE DEMO
# -----------------------------
if __name__ == '__main__':
    user_ctrl = UserController()
    expense_ctrl = ExpenseController()

    # Add users
    u1 = User("U1001", "User1")
    u2 = User("U2001", "User2")
    u3 = User("U3001", "User3")
    for user in [u1, u2, u3]:
        user_ctrl.add_user(user)

    # Equal Split Expense
    splits1 = [Split(u1, 300), Split(u2, 300), Split(u3, 300)]
    expense_ctrl.create_expense("E1", "Breakfast", 900, splits1, ExpenseSplitType.EQUAL, u1)

    # Unequal Split Expense
    splits2 = [Split(u1, 400), Split(u2, 100)]
    expense_ctrl.create_expense("E2", "Lunch", 500, splits2, ExpenseSplitType.UNEQUAL, u2)

    # Show balance sheets
    for user in user_ctrl.get_all_users():
        expense_ctrl.balance_ctrl.show_user_balance(user)
