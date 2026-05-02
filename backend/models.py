from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_no = Column(String, index=True)
    doc_name = Column(String)
    doc_type = Column(String)
    revision = Column(Integer, default=1)
    status = Column(String, default="Beklemede") # Beklemede, Onaylandı, Reddedildi, Arşivlendi
    uploader = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Audit details
    rev_reason = Column(Text, nullable=True)
    affected_op = Column(Text, nullable=True)
    diff_desc = Column(Text, nullable=True)
    
    # MinIO reference
    file_object_name = Column(String, nullable=True)
    
    approvals = relationship("Approval", back_populates="document", cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    user_name = Column(String)
    user_role = Column(String)
    status = Column(String, default="Bekliyor") # Bekliyor, Onaylandı, Reddedildi
    feedback = Column(Text, nullable=True)
    
    document = relationship("Document", back_populates="approvals")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_role = Column(String)
    action = Column(String)
    target = Column(String)
