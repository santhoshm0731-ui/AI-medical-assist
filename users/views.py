from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date

from pharmacy.models import Order
from users.models import PharmacyProfile, Medicine  # if not already imported
from .models import PatientProfile, DoctorProfile

User = get_user_model()
def home(request):
    num_patients = User.objects.filter(is_patient=True).count()
    num_doctors = User.objects.filter(is_doctor=True).count()
    num_pharmacies = PharmacyProfile.objects.count()

    return render(request, 'home.html', {
        'num_patients': num_patients,
        'num_doctors': num_doctors,
        'num_pharmacies': num_pharmacies,
    })

# near the top of users/views.py
from django.shortcuts import render, redirect


# Login View
def patient_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if getattr(user, 'is_patient', False):
                login(request, user)
                return redirect('patient_dashboard')
            else:
                messages.error(request, "This login page is only for patients.")
                return redirect('patient_login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('patient_login')

    return render(request, 'patient/patient_login.html')


def doctor_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if getattr(user, 'is_doctor', False):
                login(request, user)
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "This login page is only for doctors.")
                return redirect('doctor_login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('doctor_login')

    return render(request, 'doctor/doctor_login.html')

# Logout View
def user_logout(request):
    logout(request)
    return redirect('home')

# Register Patient
def register_patient(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        age = request.POST.get('age')
        gender = request.POST.get('gender')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register_patient')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_patient = True
        user.save()

        from .models import PatientProfile
        PatientProfile.objects.create(user=user, age=age, gender=gender)

        messages.success(request, "Patient registered successfully! Please log in.")
        return redirect('patient_login')

    return render(request, 'users/register_patient.html')

def pharmacy_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if getattr(user, 'is_pharmacy', False):
                login(request, user)
                return redirect('pharmacy_dashboard')
            else:
                messages.error(request, "This login page is only for pharmacies.")
                return redirect('pharmacy_login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('pharmacy_login')

    return render(request, 'pharmacy/pharmacy_login.html')



# Register Doctor
# users/views.py

# users/views.py

def register_pharmacy(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        pharmacy_name = request.POST.get("pharmacy_name")
        address = request.POST.get("address")
        upi_id = request.POST.get("upi_id")
        upi_qr = request.FILES.get("upi_qr")   # ✅ QR image

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register_pharmacy")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_pharmacy = True
        user.save()

        PharmacyProfile.objects.create(
            user=user,
            pharmacy_name=pharmacy_name,
            address=address,
            upi_id=upi_id,
            upi_qr=upi_qr,
        )

        messages.success(request, "Pharmacy registered successfully! Please log in.")
        return redirect("pharmacy_login")

    return render(request, "users/register_pharmacy.html")


def register_doctor(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        specialty = request.POST.get('specialty')
        fees = request.POST.get('fees')
        address = request.POST.get('address')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register_doctor')

        # Create doctor user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_doctor = True
        user.save()

        # Create doctor profile with specialization, fees, and address
        from .models import DoctorProfile
        DoctorProfile.objects.create(user=user, specialty=specialty, fees=fees, address=address)

        messages.success(request, "Doctor registered successfully! Please log in.")
        return redirect('doctor_login')

    return render(request, 'users/register_doctor.html')


# Patient Dashboard
@login_required
def patient_dashboard(request):
    if request.user.is_doctor:
        return redirect('doctor_dashboard')

    from appointments.models import Appointment
    from .models import PatientProfile

    appointments = Appointment.objects.filter(patient=request.user).order_by('date')

    profile = PatientProfile.objects.filter(user=request.user).first()

    return render(request, 'patient/dashboard.html', {
        'appointments': appointments,
        'profile': profile
    })

def admin_login(request):
    """Separate login page only for Django superuser."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                login(request, user)
                messages.success(request, "Welcome back, Admin!")
                return redirect("/analytics/admin-dashboard/")
            else:
                messages.error(request, "Access Denied — Only Superusers are allowed.")
                return redirect("admin_login")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "users/admin_login.html")


# Doctor Dashboard
@login_required
def doctor_dashboard(request):
    if not request.user.is_doctor:
        return redirect('patient_dashboard')

    from appointments.models import Appointment
    from .models import DoctorProfile

    appointments = Appointment.objects.filter(doctor=request.user).order_by('date')

    profile = DoctorProfile.objects.filter(user=request.user).first()

    return render(request, 'doctor/dashboard.html', {
        'appointments': appointments,
        'profile': profile
    })

# pharmacy/views.py

@login_required
def pharmacy_dashboard(request):
    # ensure the user is a pharmacy user
    if not getattr(request.user, "is_pharmacy", False):
        return HttpResponseForbidden("Not authorized")

    profile, _ = PharmacyProfile.objects.get_or_create(user=request.user)

    # Add medicine via dashboard POST (name field indicates add medicine)
    if request.method == "POST" and request.POST.get("name") and not request.POST.get("edit_medicine_id"):
        # adding new medicine
        name = request.POST.get("name").strip()
        try:
            quantity = int(request.POST.get("quantity", 0))
        except ValueError:
            quantity = 0
        try:
            price = Decimal(request.POST.get("price", "0"))
        except Exception:
            price = Decimal("0")
        image = request.FILES.get("image")

        Medicine.objects.create(
            pharmacy=profile,
            name=name,
            quantity=max(0, quantity),
            price=price,
            image=image
        )
        messages.success(request, "Medicine added successfully.")
        return redirect("pharmacy_dashboard")

    medicines = Medicine.objects.filter(pharmacy=profile).order_by("-created_at")
    orders = Order.objects.filter(pharmacy=profile).select_related("patient", "medicine").order_by("-created_at")

    return render(request, "pharmacy/dashboard.html", {
        "profile": profile,
        "medicines": medicines,
        "orders": orders,
    })



@login_required
def edit_patient_profile(request):
    """Patient can edit own email, age, gender."""
    if not getattr(request.user, "is_patient", False):
        messages.error(request, "Only patients can edit this profile.")
        return redirect('home')

    profile, created = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        email = request.POST.get("email")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        if email:
            request.user.email = email
            request.user.save()

        try:
            profile.age = int(age) if age else None
        except ValueError:
            profile.age = None

        profile.gender = gender or ""
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('patient_dashboard')

    context = {
        "profile": profile,
    }
    return render(request, "patient/edit_profile.html", context)


@login_required
def edit_doctor_profile(request):
    """Doctor can edit own specialty, fees, address."""
    if not getattr(request.user, "is_doctor", False):
        messages.error(request, "Only doctors can edit this profile.")
        return redirect('home')

    profile, created = DoctorProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        specialty = request.POST.get("specialty")
        fees = request.POST.get("fees")
        address = request.POST.get("address")

        profile.specialty = specialty or ""

        try:
            profile.fees = float(fees) if fees else None
        except ValueError:
            profile.fees = None

        profile.address = address or ""
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('doctor_dashboard')

    context = {
        "profile": profile,
    }
    return render(request, "doctor/edit_profile.html", context)




