from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import json

from database import engine, Base, get_db
import models
import schemas
from minio_client import minio_client, BUCKET_NAME, get_presigned_url, init_minio

# Create all tables
Base.metadata.create_all(bind=engine)
init_minio()

app = FastAPI(title="DMS API")

@app.post("/documents/", response_model=schemas.DocumentResponse)
def create_document(
    doc_no: str = Form(...),
    doc_name: str = Form(...),
    doc_type: str = Form(...),
    rev_reason: str = Form(None),
    affected_op: str = Form(None),
    diff_desc: str = Form(None),
    uploader: str = Form(...),
    approvals: str = Form(...), # JSON string of approval list
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Upload file to MinIO
    file_extension = file.filename.split(".")[-1]
    object_name = f"{doc_no}_{uuid.uuid4().hex[:8]}.{file_extension}"
    
    minio_client.put_object(
        BUCKET_NAME,
        object_name,
        file.file,
        length=-1,
        part_size=10*1024*1024,
        content_type=file.content_type
    )
    
    # Calculate revision
    existing_docs = db.query(models.Document).filter(models.Document.doc_no == doc_no).all()
    new_rev = max([d.revision for d in existing_docs]) + 1 if existing_docs else 1
    
    db_doc = models.Document(
        doc_no=doc_no,
        doc_name=doc_name,
        doc_type=doc_type,
        revision=new_rev,
        uploader=uploader,
        rev_reason=rev_reason,
        affected_op=affected_op,
        diff_desc=diff_desc,
        file_object_name=object_name
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Parse and add approvals
    approval_list = json.loads(approvals)
    for app in approval_list:
        db_app = models.Approval(
            document_id=db_doc.id,
            user_name=app['user_name'],
            user_role=app['user_role']
        )
        db.add(db_app)
    
    # Log action
    log = models.AuditLog(user_role=uploader, action="Yükledi", target=f"{doc_no} (v{new_rev})")
    db.add(log)
    
    db.commit()
    db.refresh(db_doc)
    return db_doc

@app.get("/documents/", response_model=List[schemas.DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).order_by(models.Document.id.desc()).all()

@app.get("/documents/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/documents/{doc_id}/signed-url")
def get_document_url(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc or not doc.file_object_name:
        raise HTTPException(status_code=404, detail="File not found")
    
    url = get_presigned_url(doc.file_object_name)
    return {"url": url}

@app.post("/approvals/{approval_id}/approve")
def approve_document(approval_id: int, user_name: str, db: Session = Depends(get_db)):
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = "Onaylandı"
    approval.feedback = "Uygun"
    db.commit()
    
    # Check overall status
    doc = db.query(models.Document).filter(models.Document.id == approval.document_id).first()
    all_approved = all(a.status == "Onaylandı" for a in doc.approvals)
    if all_approved:
        doc.status = "Onaylandı"
        # Archive older
        old_docs = db.query(models.Document).filter(
            models.Document.doc_no == doc.doc_no,
            models.Document.id != doc.id,
            models.Document.status == "Onaylandı"
        ).all()
        for od in old_docs:
            od.status = "Arşivlendi"
            
    # Log
    log = models.AuditLog(user_role=user_name, action="Onayladı", target=doc.doc_no)
    db.add(log)
    db.commit()
    return {"status": "success"}

@app.post("/approvals/{approval_id}/reject")
def reject_document(approval_id: int, user_name: str, feedback: str, db: Session = Depends(get_db)):
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = "Reddedildi"
    approval.feedback = feedback
    
    doc = db.query(models.Document).filter(models.Document.id == approval.document_id).first()
    doc.status = "Reddedildi"
    
    # Log
    log = models.AuditLog(user_role=user_name, action="Reddetti", target=doc.doc_no)
    db.add(log)
    
    db.commit()
    return {"status": "success"}

@app.get("/audit-logs/", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(50).all()

@app.post("/audit-logs/")
def create_audit_log(log: schemas.AuditLogCreate, db: Session = Depends(get_db)):
    db_log = models.AuditLog(**log.dict())
    db.add(db_log)
    db.commit()
    return {"status": "success"}
