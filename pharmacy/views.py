# pharmacy/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from users.models import Medicine, PharmacyProfile
from .models import Order


@login_required
def pharmacy_marketplace(request):
    medicines = Medicine.objects.select_related("pharmacy").order_by("name")
    return render(request, "pharmacy/marketplace.html", {
        "medicines": medicines,
    })


# pharmacy/views.py

@login_required
@require_POST
def place_order(request, medicine_id):
    """Create an order and reduce stock."""
    med = get_object_or_404(Medicine, id=medicine_id)

    # quantity
    try:
        qty = int(request.POST.get("quantity", "1"))
    except ValueError:
        qty = 1

    if qty < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("pharmacy_marketplace")

    if qty > med.quantity:
        messages.error(request, "Requested quantity exceeds available stock.")
        return redirect("pharmacy_marketplace")

    # payment
    payment_method = request.POST.get("payment_method", "COD").upper()
    if payment_method not in ("COD", "UPI"):
        payment_method = "COD"

    # ✅ use total_price (matches your model)
    total_price = med.price * qty  # Decimal * int

    # ✅ set pharmacy from medicine.pharmacy
    order = Order.objects.create(
        patient=request.user,
        pharmacy=med.pharmacy,
        medicine=med,
        quantity=qty,
        payment_method=payment_method,
        total_price=total_price,
    )

    # reduce stock
    med.quantity -= qty
    med.save()

    messages.success(request, f"Order #{order.id} placed successfully!")
    return redirect("patient_orders")



@login_required
def patient_orders(request):
    """Patient's view of all their medicine orders."""
    orders = Order.objects.filter(patient=request.user).select_related(
        "pharmacy", "medicine"
    ).order_by("-created_at")

    return render(request, "pharmacy/patient_orders.html", {
        "orders": orders,
    })

@login_required
def pharmacy_orders(request):
    if not getattr(request.user, "is_pharmacy", False):
        return HttpResponseForbidden("Not authorized")

    pharmacy_profile = PharmacyProfile.objects.filter(user=request.user).first()
    orders = Order.objects.filter(pharmacy=pharmacy_profile).select_related(
        "patient", "medicine"
    ).order_by("-created_at")

    return render(request, "pharmacy/pharmacy_orders.html", {
        "orders": orders,
        "pharmacy": pharmacy_profile,
    })


from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_order_status(request, order_id):
    """
    Pharmacy updates order status via dropdown on dashboard.
    Once patient has confirmed (patient_confirmed=True) OR
    status is COMPLETED/CANCELLED, order is locked.
    """
    order = get_object_or_404(Order, id=order_id)

    # ✅ ensure this is a pharmacy user & owns this order
    if not getattr(request.user, "is_pharmacy", False) or order.pharmacy.user != request.user:
        return HttpResponseForbidden("Not authorized")

    # ✅ HARD LOCK
    if order.patient_confirmed or order.status in ["COMPLETED", "CANCELLED"]:
        messages.warning(
            request,
            "This order is already completed/confirmed and cannot be modified."
        )
        return redirect("pharmacy_dashboard")

    new_status = request.POST.get("new_status")

    VALID_STATUSES = ["PENDING", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]

    if new_status not in VALID_STATUSES:
        messages.error(request, "Invalid status selected.")
        return redirect("pharmacy_dashboard")

    order.status = new_status
    order.save()
    messages.success(request, f"Order #{order.id} status updated to {new_status}.")
    return redirect("pharmacy_dashboard")



@login_required
def confirm_order_received(request, order_id):
    order = get_object_or_404(Order, id=order_id, patient=request.user)

    if request.method == "POST":
        if order.status == "DELIVERED" and not order.patient_confirmed:
            order.patient_confirmed = True
            order.status = "COMPLETED"
            order.save()
            messages.success(request, "✅ Order marked as completed. Hope you feel better soon!")
        else:
            messages.warning(request, "This order cannot be confirmed right now.")

    return redirect("patient_orders")

@login_required
def edit_pharmacy_profile(request):
    """
    Edit pharmacy profile (store name, address, upi id, qr image).
    Aligns with PharmacyProfile fields: pharmacy_name, address, upi_id, upi_qr
    """
    if not getattr(request.user, "is_pharmacy", False):
        messages.error(request, "Only pharmacy users can edit this profile.")
        return redirect('home')

    # get_or_create so new pharmacy user still gets a profile
    profile, _ = PharmacyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # use consistent field names matching the model
        pharmacy_name = request.POST.get("pharmacy_name") or request.POST.get("store_name") or profile.pharmacy_name
        address = request.POST.get("address", "")
        upi_id = request.POST.get("upi_id", "")
        qr_file = request.FILES.get("qr_code") or request.FILES.get("upi_qr")

        profile.pharmacy_name = pharmacy_name
        profile.address = address
        profile.upi_id = upi_id

        if qr_file:
            profile.upi_qr = qr_file

        profile.save()
        messages.success(request, "Pharmacy profile updated successfully.")
        return redirect('pharmacy_dashboard')

    return render(request, "pharmacy/edit_profile.html", {"profile": profile})


@login_required
def edit_medicine(request, medicine_id):
    """
    Edit an existing medicine (name, quantity, price, image).
    Only the owning pharmacy may edit.
    """
    med = get_object_or_404(Medicine, id=medicine_id)

    # locate pharmacy profile for the logged-in user
    try:
        user_pharmacy = PharmacyProfile.objects.get(user=request.user)
    except PharmacyProfile.DoesNotExist:
        return HttpResponseForbidden("Not authorized")

    if med.pharmacy != user_pharmacy:
        return HttpResponseForbidden("Not authorized to edit this medicine.")

    if request.method == "POST":
        name = request.POST.get("name", med.name)
        try:
            quantity = int(request.POST.get("quantity", med.quantity or 0))
        except (ValueError, TypeError):
            quantity = med.quantity or 0

        try:
            price_raw = request.POST.get("price", med.price)
            # preserve Decimal if model uses DecimalField
            price = price_raw if price_raw is None else price_raw
        except Exception:
            price = med.price

        image = request.FILES.get("image")

        med.name = name
        med.quantity = quantity
        med.price = price
        if image:
            med.image = image
        med.save()
        messages.success(request, "Medicine updated successfully.")
        return redirect("pharmacy_dashboard")

    return render(request, "pharmacy/edit_medicine.html", {"med": med})


@login_required
@require_POST
def clear_completed_orders(request):
    """
    Clear (delete) orders for this pharmacy with status COMPLETED / CANCELLED.
    (For safety, only pharmacy owners can delete their own orders.)
    """
    if not getattr(request.user, "is_pharmacy", False):
        messages.error(request, "Not authorized.")
        return redirect("home")

    pharmacy_profile = PharmacyProfile.objects.filter(user=request.user).first()
    if not pharmacy_profile:
        messages.error(request, "Pharmacy profile not found.")
        return redirect("home")

    # statuses to remove
    to_remove = ["COMPLETED", "CANCELLED"]
    qs = Order.objects.filter(pharmacy=pharmacy_profile, status__in=to_remove)

    count = qs.count()
    if count == 0:
        messages.info(request, "No completed/cancelled orders to clear.")
        return redirect("pharmacy_dashboard")

    # delete them
    qs.delete()
    messages.success(request, f"Cleared {count} completed/cancelled order(s).")
    return redirect("pharmacy_dashboard")
