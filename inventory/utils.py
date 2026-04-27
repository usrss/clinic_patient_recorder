"""
Inventory utility functions.

These are plain Python helpers — not view handlers — so they can be safely
imported by other apps (consultations, management commands, tests, signals)
without pulling in Django's HTTP machinery.
"""
from .models import Medicine, StockMovement


def deduct_medicine_stock(medicine_id, quantity, reason, user=None):
    """
    Deduct stock and log a StockMovement. Called by the consultations app
    when a doctor prescribes medicine. Must be called inside transaction.atomic().

    Raises:
        Medicine.DoesNotExist: if medicine_id is invalid
        ValidationError: if insufficient stock
    """
    medicine = Medicine.objects.get(pk=medicine_id)
    medicine.deduct_stock(quantity)
    StockMovement.objects.create(
        medicine=medicine,
        movement_type=StockMovement.MovementType.OUT,
        quantity=quantity,
        reason=reason,
        reference=reason,
        created_by=user.username if user else 'system',
    )
    return True