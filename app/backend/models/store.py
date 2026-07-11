from pydantic import BaseModel

class Store(BaseModel):
    store_id: int
    store_name: str
    store_city: str
    store_state: str

