from django.db import models, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q

# FIX 05: Added clinical_staff_required so doctors and front desk can view stock.
from accounts.decorators import nurse_required, admin_required, clinical_staff_required
from .models import Medicine, StockMovement
from .forms import MedicineForm, MedicineRestockForm, MedicineSearchForm


@login_required
@clinical_staff_required  # FIX 05: was @nurse_required — doctors/frontdesk need read access
def medicine_list(request):
    """List all medicines with search and filters."""
    form = MedicineSearchForm(request.GET or None)
    medicines = Medicine.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        low_stock_only = form.cleaned_data.get('low_stock_only')

        if query:
            medicines = medicines.filter(
                Q(name__icontains=query) |
                Q(generic_name__icontains=query) |
                Q(description__icontains=query)
            )
        if low_stock_only:
            medicines = medicines.filter(quantity__lte=models.F('low_stock_threshold'))

    low_stock_count = Medicine.objects.filter(
        quantity__lte=models.F('low_stock_threshold')
    ).count()

    return render(request, 'inventory/medicine_list.html', {
        'medicines': medicines,
        'form': form,
        'low_stock_count': low_stock_count,
    })


@login_required
@clinical_staff_required  # FIX 05: was @nurse_required — doctors/frontdesk need read access
def medicine_detail(request, pk):
    """View medicine details and stock history."""
    medicine = get_object_or_404(Medicine, pk=pk)
    stock_movements = medicine.stock_movements.all()[:20]
    return render(request, 'inventory/medicine_detail.html', {
        'medicine': medicine,
        'stock_movements': stock_movements,
        'is_low_stock': medicine.is_low_stock(),
    })


@login_required
@admin_required
def medicine_create(request):
    """Create a new medicine."""
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        medicine = form.save()
        messages.success(request, f'Medicine "{medicine.name}" created successfully.')
        return redirect('inventory:medicine_detail', pk=medicine.pk)
    return render(request, 'inventory/medicine_form.html', {'form': form, 'action': 'Create'})


@login_required
@admin_required
def medicine_edit(request, pk):
    """Edit an existing medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
        return redirect('inventory:medicine_detail', pk=medicine.pk)
    return render(request, 'inventory/medicine_form.html', {
        'form': form, 'action': 'Edit', 'medicine': medicine,
    })


@login_required
@nurse_required
def medicine_restock(request, pk):
    """Add stock to a medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineRestockForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                quantity = form.cleaned_data['quantity']
                reason = form.cleaned_data.get('reason', '')
                batch_number = form.cleaned_data.get('batch_number', '')
                expiry_date = form.cleaned_data.get('expiry_date')

                medicine.add_stock(quantity)

                # Update batch/expiry metadata separately if provided
                update_fields = []
                if batch_number:
                    medicine.batch_number = batch_number
                    update_fields.append('batch_number')
                if expiry_date:
                    medicine.expiry_date = expiry_date
                    update_fields.append('expiry_date')
                if update_fields:
                    medicine.save(update_fields=update_fields)

                StockMovement.objects.create(
                    medicine=medicine,
                    movement_type=StockMovement.MovementType.IN,
                    quantity=quantity,
                    reason=reason or 'Stock replenishment',
                    created_by=request.user.username,
                )

            messages.success(
                request,
                f'Added {quantity} {medicine.get_unit_display()}(s) to {medicine.name}.'
            )
            return redirect('inventory:medicine_detail', pk=medicine.pk)

        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, 'message') else str(e))
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')

    return render(request, 'inventory/medicine_restock.html', {
        'form': form, 'medicine': medicine,
    })


@login_required
@nurse_required
def medicine_deduct(request, pk):
    """Manually deduct stock from a medicine."""
    from .forms import MedicineDeductForm

    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineDeductForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                quantity = form.cleaned_data['quantity']
                reason = form.cleaned_data['reason']
                medicine.deduct_stock(quantity)
                StockMovement.objects.create(
                    medicine=medicine,
                    movement_type=StockMovement.MovementType.OUT,
                    quantity=quantity,
                    reason=reason,
                    reference=reason,
                    created_by=request.user.username,
                )
            messages.success(
                request,
                f'Dispensed {quantity} {medicine.get_unit_display()}(s) of {medicine.name}.'
            )
            return redirect('inventory:medicine_detail', pk=medicine.pk)
        except ValidationError as e:
            messages.error(request, e.message)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'inventory/medicine_deduct.html', {
        'form': form, 'medicine': medicine,
    })


@login_required
@admin_required
def medicine_delete(request, pk):
    """Delete a medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        name = medicine.name
        medicine.delete()
        messages.success(request, f'Medicine "{name}" deleted.')
        return redirect('inventory:medicine_list')
    return render(request, 'inventory/medicine_confirm_delete.html', {'medicine': medicine})


@login_required
@nurse_required
def stock_movements(request, medicine_pk=None):
    """View stock movement audit trail."""
    movements = StockMovement.objects.all().select_related('medicine')
    medicine = None
    if medicine_pk:
        medicine = get_object_or_404(Medicine, pk=medicine_pk)
        movements = movements.filter(medicine=medicine)
        title = f'Stock Movements — {medicine.name}'
    else:
        title = 'All Stock Movements'
    return render(request, 'inventory/stock_movements.html', {
        'movements': movements[:50],
        'title': title,
        'medicine': medicine,
    })
