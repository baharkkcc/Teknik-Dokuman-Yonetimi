from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ApprovalBase(BaseModel):
    user_name: str
    user_role: str

class ApprovalCreate(ApprovalBase):
    pass

class ApprovalResponse(ApprovalBase):
    id: int
    status: str
    feedback: Optional[str] = None
    class Config:
        orm_mode = True

class DocumentBase(BaseModel):
    doc_no: str
    doc_name: str
    doc_type: str
    rev_reason: Optional[str] = None
    affected_op: Optional[str] = None
    diff_desc: Optional[str] = None
    uploader: str

class DocumentCreate(DocumentBase):
    approvals: List[ApprovalCreate]

class DocumentResponse(DocumentBase):
    id: int
    revision: int
    status: str
    created_at: datetime
    file_object_name: Optional[str] = None
    approvals: List[ApprovalResponse]
    class Config:
        orm_mode = True

class AuditLogCreate(BaseModel):
    user_role: str
    action: str
    target: str

class AuditLogResponse(AuditLogCreate):
    id: int
    timestamp: datetime
    class Config:
        orm_mode = True
