from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    role = Column(String)
    departments = Column(JSON)  # List of accessible departments
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    key = Column(String, unique=True)
    description = Column(Text)
    ai_context = Column(Text)
    blocked_keywords = Column(JSON)  # List of blocked keywords
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    department = Column(String)
    user_message = Column(Text)
    ai_response = Column(Text)
    citations = Column(JSON)  # Store Perplexity citations
    created_at = Column(DateTime, default=datetime.utcnow)
