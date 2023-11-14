from sqlalchemy import event
from models import db, Fee


# setting default starting value for fee.invoice_number and incrementing it by 1
@event.listens_for(Fee, 'before_insert')
def generate_invoice_number(mapper, connection, target):
    if not target.invoice_number:
        last_invoice = (
            db.session.query(Fee)
            .order_by(Fee.id.desc())
            .first()
        )
        target.invoice_number = last_invoice.invoice_number + 1 if last_invoice else 45778