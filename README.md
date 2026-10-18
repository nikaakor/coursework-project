# Інформаційна система «Інтернет-аптека» PharmPlus (Варіант 5)

FastAPI + SQLAlchemy + SQLite, фронтенд — `frontend/index.html` (вітрина) та `frontend/admin.html` (адмін-панель), Tailwind CDN.

## Запуск

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Відкрийте http://127.0.0.1:8000 (Swagger: http://127.0.0.1:8000/docs).
Під час першого запуску створюється `database/pharmacy.db` з демо-даними. Якщо у вас лишився старий `pharmacy.db` —
видаліть його перед запуском (змінилася схема таблиць).

## Адмін-панель
Відкрийте http://127.0.0.1:8000/admin-panel (або кнопка «⚙️ Адмінка» на сайті) і введіть ключ: `admin`
(змінюється змінною середовища `ADMIN_KEY`; REST-запити передають його в заголовку `X-Admin-Key`).

| Розділ | Можливості |
|---|---|
| Огляд | виручка, середній чек, замовлення за статусами, виручка за 14 днів, топ товарів, товари, що закінчуються, клієнти за категоріями |
| Замовлення | перегляд і фільтр за статусом; зміна статусу за правилами автомата станів (State); скасування повертає товар на склад/в аптеку та коригує бонуси |
| Товари | пошук, додавання, редагування, видалення (товар з історією замовлень видалити не можна) |
| Аптеки і залишки | CRUD аптек, редагування залишків кожного товару в кожній аптеці |
| Акції | створення (на всі товари / категорію / товар) і видалення, індикатор «діє / не діє» |
| Клієнти | зміна категорії (звичайний / соціальний / преміум), ручне нарахування/списання бонусів |

Статуси замовлення: кур'єр — `new → processing → shipped → completed`; самовивіз — `reserved → ready → completed`;
з будь-якого незавершеного — `cancelled`. Клієнт отримує сповіщення про кожну зміну.

## Демо-користувачі
| Email | Категорія |
|---|---|
| taras@example.com | преміум (має рецепт на Аспірин Кардіо, нагадування про вітамін C, стеження за тонометром) |
| maria@example.com | соціальний |

## Відповідність вимогам
| Вимога | Реалізація |
|---|---|
| Каталог (ліки, вітаміни, вироби) | `GET /products/`, 3 категорії |
| Пошук за назвою/категорією/виробником | параметр `search` (регістронезалежний, у т.ч. кирилиця) |
| Фільтри ціна / рецептурність / наявність | `min_price`, `max_price`, `is_prescription`, `in_stock_only`, сортування `sort` |
| Кошик, кур'єр чи самовивіз | `POST /orders/preview`, `POST /orders/create-full` (`delivery_type`: `pickup`/`courier`) |
| Бронювання в найближчій аптеці | `GET /pharmacies/nearest`, залишки по аптеках, статус `reserved` |
| Історія замовлень, повторне замовлення | `GET /orders/user/{id}` (з позиціями), кнопка «Повторити» |
| Збережені рецепти | `GET/POST /users/{id}/prescriptions`; рецептурні товари без чинного рецепта купити не можна |
| Лояльність | бонуси: 1% / 2% / 5%; звичайний — без знижки, соціальний — 15% на «соціальні» препарати, преміум — 10% + безкоштовна доставка; списання бонусів до 30% |
| Сповіщення | `GET /users/{id}/notifications`: наявність у найближчій аптеці, нагадування про регулярні препарати, акції |
| Акції та сезонні знижки | таблиця `promotions` (товар або категорія + період дії), `POST /admin/promotions/` |

## Патерни
- **Strategy** (`patterns.py`) — `RegularDiscount`, `SocialDiscount`, `PremiumDiscount`
- **Builder** — `OrderBuilder` рахує суму, знижки, доставку, бонуси
- **Observer** — `OrderSubject` + `DbNotifier`, `EmailNotifier`, `SmsNotifier` (оформлення замовлення та зміна його статусу)
- **State** — `OrderState` + `New/Processing/Shipped/Reserved/Ready/Completed/CancelledState` (дозволені переходи статусів, `get_state` — проста фабрика)

## Структура
```
backend/
  main.py            точка входу (збирає роутери, lifespan, обробник помилок)
  routers/           HTTP-шар (контролери): catalog, users, orders, pharmacies, admin
  services/          бізнес-логіка: OrderService (Facade), CatalogService, UserService, NotificationService,
                     AdminService, AdminOrderService (State), ReportService (дашборд)
  repositories/      доступ до БД (Repository)
  patterns.py        Strategy, Builder, Observer, State, Factory
  models.py          ORM-моделі          schemas.py   DTO (pydantic)
  deps.py            Dependency Injection  exceptions.py / config.py / database.py / seed.py
frontend/
  index.html         вітрина             admin.html   адмін-панель (/admin-panel)
database/            pharmacy.db (створюється автоматично, не в git)
docs/ANALYSIS.md     Use Case, діаграми класів, патерни, архітектура
```
