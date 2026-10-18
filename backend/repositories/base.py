from sqlalchemy.orm import Session


class Repository:
    """Базовий репозиторій. Усі репозиторії одного запиту ділять одну сесію (= одна транзакція)."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, obj):
        self.db.add(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()

    def refresh(self, obj):
        self.db.refresh(obj)
