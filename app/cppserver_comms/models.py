from pydantic import BaseModel
from typing import Optional

class BasicMessageModel(BaseModel):
    message: str

class ConfirmationModel(BaseModel):
    action: str
    status: str

class ISBActionModel(BaseModel):
    component: str
    action: str
    data: Optional[str] = None

class MessageModel(BaseModel):
    type: str
    basic_message: Optional[BasicMessageModel] = None
    confirmation: Optional[ConfirmationModel] = None
    isb_action: Optional[ISBActionModel] = None