from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count
from django.http import HttpResponse

from appointments.views import User
from .models import HealthRecord
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from appointments.models import Appointment


User = get_user_model()

@login_required(login_url='/users/login/doctor/')
def admin_analytics_dashboard(request):
    """Only superusers can access the admin analytics dashboard."""
    if not request.user.is_superuser:
        return render(request, "analytics/access_denied.html", status=403)

    # === Analytics logic for superuser ===
    total_users = User.objects.count()
    total_patients = User.objects.filter(is_patient=True).count()
    total_doctors = User.objects.filter(is_doctor=True).count()
    total_pharmacies = User.objects.filter(is_pharmacy=True).count()
    total_appointments = Appointment.objects.count()

    appointments_by_status = (
        Appointment.objects.values('status')
        .annotate(count=Count('status'))
    )

    top_doctors = (
        Appointment.objects.values('doctor__username')
        .annotate(count=Count('doctor'))
        .order_by('-count')[:5]
    )

    top_patients = (
        Appointment.objects.values('patient__username')
        .annotate(count=Count('patient'))
        .order_by('-count')[:5]
    )

    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_pharmacies': total_pharmacies,
        'total_appointments': total_appointments,
        'appointments_by_status': appointments_by_status,
        'top_doctors': top_doctors,
        'top_patients': top_patients,
    }

    return render(request, 'analytics/admin_dashboard.html', context)


@login_required(login_url='/users/login/admin/')
def view_all_patients(request):
    """Show all registered patients (superuser only)."""
    if not request.user.is_superuser:
        return render(request, "analytics/access_denied.html", status=403)

    patients = User.objects.filter(is_patient=True)
    return render(request, "analytics/view_patients.html", {"patients": patients})


@login_required(login_url='/users/login/admin/')
def view_all_doctors(request):
    """Show all registered doctors (superuser only)."""
    if not request.user.is_superuser:
        return render(request, "analytics/access_denied.html", status=403)

    doctors = User.objects.filter(is_doctor=True)
    return render(request, "analytics/view_doctors.html", {"doctors": doctors})

# =======================
#   ANALYTICS DASHBOARD
# =======================
@login_required
def analytics_dashboard(request):
    """Display user's health analytics summary and recent records."""
    records_qs = HealthRecord.objects.filter(user=request.user).order_by('-date')
    records = list(records_qs[:10])  # Recent 10 records

    if not records:
        return render(request, 'analytics/analytics.html', {
            'has_records': False,
            'message': "No health records found.",
        })

    # Summary calculations
    summary = {
        'total_records': len(records),
        'avg_weight': records_qs.aggregate(Avg('weight_kg'))['weight_kg__avg'],
        'avg_bmi': records_qs.aggregate(Avg('bmi'))['bmi__avg'],
        'avg_sugar': records_qs.aggregate(Avg('sugar'))['sugar__avg'],
        'avg_oxygen': records_qs.aggregate(Avg('oxygen'))['oxygen__avg'],
        'avg_heartrate': records_qs.aggregate(Avg('heartrate'))['heartrate__avg'],
        'trend': 'stable'
    }

    # Detect weight trend
    if len(records) > 1:
        latest = records[0].weight_kg or 0
        oldest = records[-1].weight_kg or 0
        if latest > oldest:
            summary['trend'] = 'up'
        elif latest < oldest:
            summary['trend'] = 'down'

    context = {
        'has_records': True,
        'summary': summary,
        'recent_records': records[::-1],  # Reverse order for chronological display
    }
    return render(request, 'analytics/analytics.html', context)


# =======================
#   DOWNLOAD PDF REPORT
# =======================
@login_required
def download_health_report(request):
    """Generate PDF health report using xhtml2pdf (Windows-safe)."""
    records = HealthRecord.objects.filter(user=request.user).order_by('-date')

    if not records.exists():
        return HttpResponse("No records to generate report.", status=404)

    summary = {
        'total_records': records.count(),
        'avg_weight': records.aggregate(Avg('weight_kg'))['weight_kg__avg'],
        'avg_bmi': records.aggregate(Avg('bmi'))['bmi__avg'],
        'avg_sugar': records.aggregate(Avg('sugar'))['sugar__avg'],
        'avg_oxygen': records.aggregate(Avg('oxygen'))['oxygen__avg'],
        'avg_heartrate': records.aggregate(Avg('heartrate'))['heartrate__avg'],
    }

    # Render HTML to PDF
    template_path = 'analytics/pdf_report.html'
    context = {
        'user': request.user,
        'records': records,
        'summary': summary,
    }
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Health_Report_{request.user.username}.pdf"'

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response.write(result.getvalue())
        return response
    return HttpResponse("Error while generating PDF", status=500)


# =======================
#   CLEAR HEALTH RECORDS
# =======================
@login_required
def clear_health_records(request):
    """Delete all of the user's saved health records."""
    if request.method == "POST":
        HealthRecord.objects.filter(user=request.user).delete()
        return redirect('analytics_dashboard')
    return HttpResponse("Invalid request method.", status=400)


@login_required(login_url='/users/login/admin/')
def manage_users(request):
    """Admin panel to view/add/delete users (only for superuser)."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')

    # Handle Add User Form
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        role = request.POST.get("role")

        if not username or not email:
            messages.error(request, "All fields are required.")
        else:
            new_user = User.objects.create_user(username=username, email=email, password="password123")
            if role == "doctor":
                new_user.is_doctor = True
            elif role == "patient":
                new_user.is_patient = True
            elif role == "pharmacy":
                new_user.is_pharmacy = True
            new_user.save()
            messages.success(request, f"✅ {role.capitalize()} '{username}' added successfully!")

        return redirect('manage_users')

    return render(request, "analytics/manage_users.html", {"users": users})


@login_required(login_url='/users/login/admin/')
def delete_user(request, user_id):
    """Allow admin to delete any user."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect('home')

    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "You cannot delete another superuser!")
    else:
        user.delete()
        messages.success(request, f"🗑️ User '{user.username}' deleted successfully.")
    return redirect('manage_users')

@login_required(login_url='/users/login/admin/')
def view_all_pharmacies(request):
    """Show all registered pharmacies (superuser only)."""
    if not request.user.is_superuser:
        return render(request, "analytics/access_denied.html", status=403)

    pharmacies = User.objects.filter(is_pharmacy=True)
    return render(request, "analytics/view_pharmacies.html", {"pharmacies": pharmacies})
