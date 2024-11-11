from sqlalchemy import Column, String
from database import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    key = Column(String, primary_key=True)  
    description = Column(String)           
