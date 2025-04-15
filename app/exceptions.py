from fastapi import HTTPException


class ServiceException(HTTPException):
    def __init__(self, status_code=400, detail=...):
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return self.detail
