from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    cep = Column(String, nullable=True)
    address = Column(String, nullable=True)       # logradouro
    number = Column(String, nullable=True)        # número da residência
    complement = Column(String, nullable=True)    # complemento
    district = Column(String, nullable=True)      # bairro
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
