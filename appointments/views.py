from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Appointment, AppointmentMessage
from django.views.decorators.http import require_http_methods
from users.models import User, DoctorProfile  # ✅ custom user model
from datetime import date
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()


@login_required
def book_appointment(request):
    """
    Show a searchable list of doctors. Patient selects a doctor and date to book.
    Only allow booking for today or a future date.
    """
    q = request.GET.get('q', '').strip()
    doctors = User.objects.filter(is_doctor=True)

    if q:
        doctors = doctors.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(doctorprofile__specialty__icontains=q) |
            Q(doctorprofile__address__icontains=q)
        ).distinct()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        date_str = request.POST.get('date')  # format 'YYYY-MM-DD'

        if not doctor_id or not date_str:
            messages.error(request, "Please fill all fields.")
            return redirect('book_appointment')

        # 👉 Simple, safe server-side check
        today_str = date.today().isoformat()  # e.g. '2025-11-19'

        # If picked date is before today → reject
        if date_str < today_str:
            messages.error(request, "Please choose today or a future date.")
            return redirect('book_appointment')

        # Django can store 'YYYY-MM-DD' string into DateField
        Appointment.objects.create(
            doctor_id=doctor_id,
            patient=request.user,
            date=date_str,
            status='Pending'
        )
        messages.success(request, "Appointment booked successfully!")
        return redirect('patient_dashboard')

    doctors = doctors.select_related('doctorprofile')

    context = {
        'doctors': doctors,
        'q': q,
        'today': date.today().isoformat(),  # used by template for min=""
    }
    return render(request, 'appointments/book_appointment.html', context)

# Doctor: manage appointments
@login_required
@require_POST
def manage_appointment(request, appointment_id, action):
    """
    Doctor actions: approve / complete / reject (cancel by doctor).
    Only the doctor for the appointment can perform actions.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    if action == 'approve':
        appointment.status = 'Approved'
        messages.success(request, "Appointment approved.")
    elif action == 'complete':
        appointment.status = 'Completed'
        messages.success(request, "Appointment marked as completed.")
    elif action == 'cancel':
        # Doctor-initiated cancellation -> reflect as Rejected for patient
        appointment.status = 'Rejected'
        messages.success(request, "Appointment rejected.")
    else:
        messages.error(request, "Unknown action.")

    appointment.save()
    return redirect('doctor_dashboard')


@login_required
@require_POST
def cancel_appointment_patient(request, appointment_id):
    """
    Let a patient cancel THEIR OWN appointment,
    but only if it's still Pending.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if appointment.status != 'Pending':
        messages.error(request, "You can only cancel appointments that are still pending.")
        return redirect('patient_dashboard')

    appointment.status = 'Cancelled'   # new status for patient cancellation
    appointment.save()
    messages.success(request, "Your appointment has been cancelled.")
    return redirect('patient_dashboard')


@login_required
@require_http_methods(["GET", "POST"])
def chat_view(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user not in (appointment.doctor, appointment.patient):
        return redirect("home")

    chat_with = appointment.patient if request.user == appointment.doctor else appointment.doctor

    if request.method == "POST":
        text = request.POST.get("message", "").strip()
        if text:
            AppointmentMessage.objects.create(
                appointment=appointment,
                sender=request.user,
                message=text
            )
        # ❌ NO redirect — just reload page
        # ❌ NO messages.success()

    messages_qs = AppointmentMessage.objects.filter(
        appointment=appointment
    ).order_by("timestamp")

    return render(request, "appointments/chat_room.html", {
        "appointment": appointment,
        "messages": messages_qs,
        "chat_with": chat_with,
    })


@csrf_exempt
@login_required
def send_message(request, appointment_id):
    if request.method == "POST":
        text = request.POST.get("message")
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if appointment.status != "Approved":
            return JsonResponse({"status": "error", "msg": "Not allowed"})

        msg = AppointmentMessage.objects.create(
            appointment=appointment,
            sender=request.user,
            message=text  # ✅ correct
        )

        return JsonResponse({
            "status": "success",
            "sender": request.user.username,
            "message": msg.message,
            "time": msg.timestamp.strftime("%H:%M"),
        })

    return JsonResponse({"status": "error"})

@login_required
@require_POST
def clear_completed_patient(request):
    """
    Patient: clear all their appointments that are Completed / Rejected / Cancelled.
    """
    deleted_count, _ = Appointment.objects.filter(
        patient=request.user,
        status__in=['Completed', 'Rejected', 'Cancelled']
    ).delete()

    if deleted_count:
        messages.success(request, f"✅ Cleared {deleted_count} old appointment(s).")
    else:
        messages.info(request, "No completed, rejected, or cancelled appointments to clear.")

    return redirect('patient_dashboard')


@login_required
@require_POST
def clear_completed_doctor(request):
    """
    Doctor: clear all their appointments that are Completed / Rejected / Cancelled.
    """
    deleted_count, _ = Appointment.objects.filter(
        doctor=request.user,
        status__in=['Completed', 'Rejected', 'Cancelled']
    ).delete()

    if deleted_count:
        messages.success(request, f"✅ Cleared {deleted_count} old appointment(s).")
    else:
        messages.info(request, "No completed, rejected, or cancelled appointments to clear.")

    return redirect('doctor_dashboard')





