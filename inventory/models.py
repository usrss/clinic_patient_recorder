from django.db import models
from django.core.exceptions import ValidationError


class Medicine(models.Model):
    """Medicine/drug inventory item."""

    class Unit(models.TextChoices):
        TABLET = 'tablet', 'Tablet'
        CAPSULE = 'capsule', 'Capsule'
        SYRUP = 'syrup', 'Syrup (ml)'
        INJECTION = 'injection', 'Injection (ml)'
        POWDER = 'powder', 'Powder (g)'
        CREAM = 'cream', 'Cream (g)'
        DROPS = 'drops', 'Drops (ml)'
        PIECE = 'piece', 'Piece'

    name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Medicine name (e.g., Paracetamol 500mg)'
    )
    generic_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Generic/chemical name'
    )
    description = models.TextField(
        blank=True,
        help_text='Uses, side effects, etc.'
    )

    # Stock management
    quantity = models.PositiveIntegerField(
        default=0,
        help_text='Current stock quantity'
    )
    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.TABLET,
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text='Alert when stock falls below this'
    )

    # Additional info
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Cost price per unit'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.quantity} {self.get_unit_display()})'

    def is_low_stock(self):
        """Check if stock is at or below threshold."""
        return self.quantity <= self.low_stock_threshold

    def deduct_stock(self, amount):
        """
        Reduce stock by amount atomically using SELECT FOR UPDATE to prevent
        race conditions where two concurrent prescriptions could both read the
        same quantity and both succeed, resulting in negative effective stock.

        Must be called inside a transaction.atomic() block.
        Raises ValidationError if insufficient stock.
        """
        # FIX: Use select_for_update() to lock the row until the transaction
        # commits, preventing concurrent reads from seeing stale quantity.
        medicine = Medicine.objects.select_for_update().get(pk=self.pk)
        if amount > medicine.quantity:
            raise ValidationError(
                f'Cannot dispense {amount} {medicine.get_unit_display()}(s). '
                f'Only {medicine.quantity} in stock.'
            )
        # FIX: Use F() expression for the update — avoids the read-modify-write
        # pattern entirely; the subtraction happens in the database in one statement.
        Medicine.objects.filter(pk=self.pk).update(quantity=models.F('quantity') - amount)
        # Refresh self so callers see the updated quantity
        self.refresh_from_db(fields=['quantity'])

    def add_stock(self, amount):
        """
        Increase stock by amount.
        FIX: Uses F() expression like deduct_stock for consistency and safety.
        """
        Medicine.objects.filter(pk=self.pk).update(quantity=models.F('quantity') + amount)
        self.refresh_from_db(fields=['quantity'])

    class Meta:
        verbose_name = 'Medicine'
        verbose_name_plural = 'Medicines'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['quantity']),
        ]


class StockMovement(models.Model):
    """Track all stock movements (in/out) for audit trail."""

    class MovementType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        EXPIRED = 'expired', 'Expired/Removed'

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(
        max_length=200, blank=True,
        help_text='Why stock was added/removed'
    )
    reference = models.CharField(
        max_length=100, blank=True,
        help_text='Consultation ID, receipt number, etc.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(
        max_length=100, blank=True,
        help_text='Username of who made the movement'
    )

    def __str__(self):
        return f'{self.medicine.name} - {self.get_movement_type_display()} ({self.quantity})'

    class Meta:
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
        ]