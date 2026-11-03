from sqlalchemy.orm import Session
from app.models.content import Enquiry
from app.models.audit import AuditLog
from app.schemas.content import EnquiryCreate, EnquiryUpdateStatus

class CRMService:
    @staticmethod
    def calculate_lead_score(enquiry_data: EnquiryCreate) -> int:
        score = 40
        # High-intent indicators
        if enquiry_data.budget and enquiry_data.budget in ["$25k - $50k", "$50k - $100k", "$100k+"]:
            score += 25
        elif enquiry_data.budget and enquiry_data.budget != "Under $5k":
            score += 15
        
        if enquiry_data.company and len(enquiry_data.company.strip()) > 2:
            score += 15
            
        if enquiry_data.timeline in ["Immediate (1-2 weeks)", "1 month"]:
            score += 15
            
        if enquiry_data.service_interest:
            score += 10
            
        msg_len = len(enquiry_data.message.strip())
        if msg_len > 100:
            score += 10
            
        return min(score, 100)

    @classmethod
    def create_enquiry(cls, db: Session, enquiry_in: EnquiryCreate) -> Enquiry:
        score = cls.calculate_lead_score(enquiry_in)
        status_val = "qualified" if score >= 70 else "new"
        
        # Qualification notes generated automatically
        notes = f"AI Auto-Score: {score}/100. Budget: {enquiry_in.budget or 'Not specified'}. Timeline: {enquiry_in.timeline or 'Not specified'}."
        
        db_enquiry = Enquiry(
            name=enquiry_in.name,
            email=enquiry_in.email,
            company=enquiry_in.company,
            industry=enquiry_in.industry,
            service_interest=enquiry_in.service_interest,
            budget=enquiry_in.budget,
            timeline=enquiry_in.timeline,
            message=enquiry_in.message,
            status=status_val,
            lead_score=score,
            qualification_notes=notes
        )
        db.add(db_enquiry)
        db.commit()
        db.refresh(db_enquiry)
        
        # Audit log
        audit = AuditLog(
            action="NEW_LEAD_SUBMISSION",
            entity="enquiry",
            entity_id=str(db_enquiry.id),
            details=f"Lead from {db_enquiry.name} ({db_enquiry.email}) with score {score}"
        )
        db.add(audit)
        db.commit()
        
        return db_enquiry

    @classmethod
    def update_status(cls, db: Session, enquiry_id: int, update_data: EnquiryUpdateStatus, user_email: str) -> Enquiry:
        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
        if not enquiry:
            return None
        enquiry.status = update_data.status
        if update_data.assigned_to:
            enquiry.assigned_to = update_data.assigned_to
        if update_data.qualification_notes:
            enquiry.qualification_notes = update_data.qualification_notes
        
        db.commit()
        db.refresh(enquiry)
        
        audit = AuditLog(
            action="LEAD_STATUS_UPDATE",
            entity="enquiry",
            entity_id=str(enquiry.id),
            user_email=user_email,
            details=f"Status set to {update_data.status}, assigned to {update_data.assigned_to}"
        )
        db.add(audit)
        db.commit()
        return enquiry
