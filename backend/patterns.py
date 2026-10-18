"""Патерни проєкту: Strategy (лояльність), Observer (сповіщення), Builder (замовлення), State (статуси замовлення)."""
from abc import ABC, abstractmethod

import models

class LoyaltyStrategy(ABC):
    label = ""
    bonus_rate = 0.01  
    free_delivery = False

    @abstractmethod
    def discount_rate(self, product) -> float:
        """Частка знижки (0..1) на конкретний товар."""


class RegularDiscount(LoyaltyStrategy):
    label = "Звичайний"
    bonus_rate = 0.01

    def discount_rate(self, product) -> float:
        return 0.0


class SocialDiscount(LoyaltyStrategy):
    label = "Соціальний"
    bonus_rate = 0.02

    def discount_rate(self, product) -> float:
        return 0.15 if product.is_social else 0.0 


class PremiumDiscount(LoyaltyStrategy):
    label = "Преміум"
    bonus_rate = 0.05
    free_delivery = True

    def discount_rate(self, product) -> float:
        return 0.10


def get_strategy(loyalty_type: str) -> LoyaltyStrategy:
    return {"social": SocialDiscount, "premium": PremiumDiscount}.get(loyalty_type, RegularDiscount)()


class NotificationObserver(ABC):
    @abstractmethod
    def update(self, message: str, kind: str = "order"):
        ...


class EmailNotifier(NotificationObserver):
    def update(self, message: str, kind: str = "order"):
        print(f"[EMAIL клієнту]: {message}")


class SmsNotifier(NotificationObserver):
    def update(self, message: str, kind: str = "order"):
        print(f"[SMS клієнту]: {message}")


class DbNotifier(NotificationObserver):
    """Зберігає сповіщення в БД — їх показує дзвіночок у кабінеті."""
    def __init__(self, repository, user_id: int):
        self.repository, self.user_id = repository, user_id

    def update(self, message: str, kind: str = "order"):
        self.repository.add(models.Notification(user_id=self.user_id, kind=kind, message=message))


class OrderSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer: NotificationObserver):
        self._observers.append(observer)

    def notify(self, message: str, kind: str = "order"):
        for o in self._observers:
            o.update(message, kind)


DELIVERY_FEE = 60.0
FREE_DELIVERY_FROM = 500.0 
MAX_BONUS_SHARE = 0.30   


class OrderBuilder:
    def __init__(self):
        self.reset()

    def reset(self):
        self._user = None
        self._strategy = RegularDiscount()
        self._lines = []
        self._delivery_type = "pickup"
        self._pharmacy = None
        self._address = ""
        self._bonus_request = 0.0

    def set_user(self, user):
        self._user = user
        self._strategy = get_strategy(user.loyalty_type)
        return self

    def set_delivery(self, delivery_type, pharmacy=None, address=""):
        self._delivery_type, self._pharmacy, self._address = delivery_type, pharmacy, address
        return self

    def add_item(self, product, quantity: int, discount_rate: float):
        self._lines.append({"product": product, "quantity": quantity, "rate": discount_rate})
        return self

    def use_bonuses(self, amount: float):
        self._bonus_request = max(0.0, amount or 0.0)
        return self

    @property
    def strategy(self):
        return self._strategy

    def get_result(self):
        subtotal = sum(l["product"].price * l["quantity"] for l in self._lines)
        discount = sum(l["product"].price * l["quantity"] * l["rate"] for l in self._lines)
        goods = subtotal - discount

        if self._delivery_type == "pickup" or self._strategy.free_delivery or goods >= FREE_DELIVERY_FROM:
            fee = 0.0
        else:
            fee = DELIVERY_FEE

        bonus_spent = min(self._bonus_request, self._user.bonus_points or 0.0, goods * MAX_BONUS_SHARE)
        paid_for_goods = goods - bonus_spent
        result = {
            "lines": self._lines,
            "delivery_type": self._delivery_type,
            "pharmacy": self._pharmacy,
            "address": self._address,
            "subtotal": round(subtotal, 2),
            "discount_total": round(discount, 2),
            "delivery_fee": fee,
            "bonus_spent": round(bonus_spent, 2),
            "bonus_earned": round(paid_for_goods * self._strategy.bonus_rate, 2),
            "total_price": round(paid_for_goods + fee, 2),
            "loyalty_label": self._strategy.label,
        }
        self.reset()
        return result



class OrderState(ABC):
    """Кожен статус сам знає, у які статуси замовлення може перейти далі."""
    name = ""
    label = ""
    next_states = ()
    notify_text = "" 

    def can_move_to(self, target: str) -> bool:
        return target in self.next_states

    @property
    def is_final(self) -> bool:
        return not self.next_states


class NewState(OrderState):          
    name, label = "new", "Нове"
    next_states = ("processing", "cancelled")


class ProcessingState(OrderState):
    name, label = "processing", "Комплектується"
    next_states = ("shipped", "cancelled")
    notify_text = "комплектується до відправлення"


class ShippedState(OrderState):
    name, label = "shipped", "Передано кур'єру"
    next_states = ("completed", "cancelled")
    notify_text = "передано кур'єру — очікуйте доставку"


class ReservedState(OrderState):   
    name, label = "reserved", "Заброньовано"
    next_states = ("ready", "cancelled")


class ReadyState(OrderState):
    name, label = "ready", "Готове до видачі"
    next_states = ("completed", "cancelled")
    notify_text = "готове до видачі в аптеці"


class CompletedState(OrderState):
    name, label = "completed", "Виконано"
    notify_text = "виконано. Дякуємо, що обрали PharmPlus!"


class CancelledState(OrderState):
    name, label = "cancelled", "Скасовано"
    notify_text = "скасовано. Бонуси повернуто, товар повернуто на залишки"


_STATES = {s.name: s for s in (NewState, ProcessingState, ShippedState, ReservedState,
                               ReadyState, CompletedState, CancelledState)}


def get_state(status: str) -> OrderState:
    """Simple Factory для станів замовлення."""
    cls = _STATES.get(status)
    if cls is None:
        raise ValueError(f"Невідомий статус: {status}")
    return cls()


ORDER_STATUSES = tuple(_STATES)
