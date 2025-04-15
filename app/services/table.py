from app.infra.repository.table import TableRepository


class TableService:
    def __init__(self):
        self.repo = TableRepository()