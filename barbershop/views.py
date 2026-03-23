from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from datetime import timedelta
import json

from .models import Client, Service, FileAttente, Paiement, SalonSettings
from .forms import ClientForm, ServiceForm, SalonSettingsForm
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth import authenticate, login, logout

# ---------------------------------
# DASHBOARD
# ---------------------------------
@login_required
@role_required(['admin'])
def dashboard(request):
    salon = SalonSettings.objects.first()
    today = timezone.now().date()

    # Statistiques
    total_clients = Client.objects.count()
    total_files = FileAttente.objects.filter(status="en_file").count()
    paiements_today = Paiement.objects.filter(date_paiement__date=today)
    total_paiements_today_count = paiements_today.count()
    total_paiements_today_somme = float(paiements_today.aggregate(total=Sum("montant"))["total"] or 0)
    total_paiements_somme = float(Paiement.objects.aggregate(total=Sum("montant"))["total"] or 0)

    # Activités récentes
    recent_files = FileAttente.objects.order_by("-date_creation")[:5]
    recent_paiements = Paiement.objects.order_by("-date_paiement")[:5]

    # Graphiques 7 derniers jours
    paiements_last7days_labels = []
    paiements_last7days_data = []
    files_last7days_labels = []
    files_last7days_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        paiements_day_decimal = Paiement.objects.filter(date_paiement__date=day).aggregate(total=Sum("montant"))["total"] or 0
        paiements_last7days_data.append(float(paiements_day_decimal))
        files_last7days_data.append(FileAttente.objects.filter(date_creation__date=day, status="en_file").count())
        label = day.strftime("%d %b")
        paiements_last7days_labels.append(label)
        files_last7days_labels.append(label)

    context = {
        "total_clients": total_clients,
        "total_files": total_files,
        "total_paiements_today_count": total_paiements_today_count,
        "total_paiements_today_somme": total_paiements_today_somme,
        "total_paiements_somme": total_paiements_somme,
        "recent_files": recent_files,
        "recent_paiements": recent_paiements,
        "paiements_last7days_labels": json.dumps(paiements_last7days_labels),
        "paiements_last7days_data": json.dumps(paiements_last7days_data),
        "files_last7days_labels": json.dumps(files_last7days_labels),
        "files_last7days_data": json.dumps(files_last7days_data),
        "salon": salon,
    }
    return render(request, "dashboard/dashboard.html", context)


# ---------------------------------
# CLIENTS CRUD
# ---------------------------------
@login_required
@role_required(['admin', 'gerant'])
@csrf_exempt
def clients_crud(request):
    clients = Client.objects.all()

    # AJOUT / MODIFICATION
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = ClientForm(request.POST, instance=client)
        else:
            form = ClientForm(request.POST)

        if form.is_valid():
            client = form.save()
            return JsonResponse({
                "status": "success",
                "client": {
                    "id": client.id,
                    "nom": client.nom,
                    "prenom": client.prenom,
                    "telephone": client.telephone,
                    "adresse": client.adresse
                }
            })
        else:
            return JsonResponse({"status": "error", "errors": form.errors})

    # SUPPRESSION AJAX
    if request.method == "DELETE":
        try:
            body = json.loads(request.body.decode("utf-8"))
            client_id = body.get("client_id")
            client = get_object_or_404(Client, id=client_id)
            client.delete()
            return JsonResponse({"status": "deleted", "client_id": client_id})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "JSON invalide"}, status=400)

    # AFFICHAGE PAGE
    form = ClientForm()
    return render(request, "clients_crud.html", {"clients": clients, "form": form})


# ---------------------------------
# SERVICES CRUD
# ---------------------------------
@login_required
@role_required(['admin', 'gerant'])
@csrf_exempt
def services_crud(request):
    services = Service.objects.all()

    # AJOUT / MODIFICATION
    if request.method == "POST":
        service_id = request.POST.get("service_id")
        if service_id:
            service = get_object_or_404(Service, id=service_id)
            form = ServiceForm(request.POST, request.FILES, instance=service)
        else:
            form = ServiceForm(request.POST, request.FILES)

        if form.is_valid():
            service = form.save()
            data = {
                "id": service.id,
                "nom": service.nom,
                "prix": str(service.prix),
                "image": service.image.url if service.image else ""
            }
            return JsonResponse({"status": "success", "service": data})
        else:
            return JsonResponse({"status": "error", "errors": form.errors})

    # SUPPRESSION AJAX
    if request.method == "DELETE":
        body = json.loads(request.body)
        service_id = body.get("service_id")
        service = get_object_or_404(Service, id=service_id)
        service.delete()
        return JsonResponse({"status": "deleted", "service_id": service_id})

    return render(request, "services/services_crud.html", {"services": services})


# ---------------------------------
# FILE ATTENTE CRUD
# ---------------------------------
@login_required
@role_required(['admin', 'gerant'])
@csrf_exempt
def file_attente_crud(request):
    files = FileAttente.objects.all()
    files_en_file = files.filter(status='en_file')
    clients_en_file = files_en_file.values_list('client_id', flat=True)
    clients = Client.objects.exclude(id__in=clients_en_file)
    services = Service.objects.all()

    if request.method == "POST":
        client_id = request.POST.get("client")
        service_id = request.POST.get("service")
        file_id = request.POST.get("file_id")
        if not service_id or (not client_id and not file_id):
            return JsonResponse({"status": "error", "errors": "Client ou service manquant"})

        service = get_object_or_404(Service, id=service_id)

        if file_id:
            file_obj = get_object_or_404(FileAttente, id=file_id)
            if file_obj.status == "en_file":
                file_obj.service = service
                file_obj.save()
            else:
                return JsonResponse({"status": "error", "errors": "Impossible de modifier ce client, il est déjà sorti"})
        else:
            client = get_object_or_404(Client, id=client_id)
            file_obj = FileAttente.objects.create(client=client, service=service)

        data = {
            "id": file_obj.id,
            "client": str(file_obj.client),
            "service": str(file_obj.service),
            "date_creation": file_obj.date_creation.strftime("%Y-%m-%d %H:%M"),
            "status": file_obj.status,
        }
        return JsonResponse({"status": "success", "file": data})

    if request.method == "DELETE":
        body = json.loads(request.body)
        file_id = body.get("file_id")
        file_obj = get_object_or_404(FileAttente, id=file_id)
        file_obj.delete()
        return JsonResponse({"status": "deleted", "file_id": file_id})

    return render(request, "file_attente/file_attente_crud.html", {"files": files, "clients": clients, "services": services})


@csrf_exempt
def file_attente_sortir(request):
    if request.method == "POST":
        file_id = request.POST.get("file_id")
        file_obj = get_object_or_404(FileAttente, id=file_id)
        paiement_non_fait = not file_obj.paiement_effectue
        file_obj.status = "sorti"
        file_obj.save()
        data = {"status": "success"}
        if paiement_non_fait:
            data["alert"] = "Attention ! Le paiement n'a pas encore été effectué."
        return JsonResponse(data)
    return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=400)


# ---------------------------------
# PAIEMENTS
# ---------------------------------
@login_required
@role_required(['admin', 'gerant'])
def paiement_validation(request):
    if request.method == "POST":
        file_id = request.POST.get("file_id")
        file_obj = get_object_or_404(FileAttente, id=file_id)
        file_obj.paiement_effectue = True
        file_obj.status = "sorti"
        file_obj.save()
        messages.success(request, "Paiement validé avec succès.")
        return redirect("paiement_validation")

    files_en_file = FileAttente.objects.filter(paiement_effectue=False).order_by("date_creation")
    return render(request, "paiements/paiements_validation.html", {"files_en_file": files_en_file})


@login_required
@role_required(['admin', 'gerant'])
def paiements_crud(request):
    if request.method == "POST":
        file_id = request.POST.get("file_id")
        client_id = request.POST.get("client_id")
        service_id = request.POST.get("service_id")

        if not file_id or not client_id or not service_id:
            messages.error(request, "Données manquantes pour le paiement.")
            return redirect("paiement_validation")

        file_obj = get_object_or_404(FileAttente, id=file_id)

        if str(file_obj.client.id) != client_id or str(file_obj.service.id) != service_id:
            messages.error(request, "Les informations du client ou du service ne correspondent pas.")
            return redirect("paiement_validation")

        if not file_obj.paiement_effectue:
            file_obj.paiement_effectue = True
            file_obj.status_paiement = "effectue"
            file_obj.save()
            Paiement.objects.create(file=file_obj, montant=file_obj.service.prix, date_paiement=timezone.now())
            messages.success(request, f"Le paiement pour {file_obj.client.nom} {file_obj.client.prenom} a été effectué !")
        else:
            messages.warning(request, f"Le paiement pour {file_obj.client.nom} {file_obj.client.prenom} a déjà été effectué.")

        return redirect("paiement_validation")

    messages.error(request, "Méthode non autorisée.")
    return redirect("paiement_validation")


# ---------------------------------
# PARAMÈTRES SALON
# ---------------------------------
@login_required
@role_required(['admin'])
def settings_salon(request):
    salon, created = SalonSettings.objects.get_or_create(id=1)
    if request.method == "POST":
        form = SalonSettingsForm(request.POST, request.FILES, instance=salon)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres du salon mis à jour !")
            return redirect('settings_salon')
        else:
            messages.error(request, "Erreur lors de la mise à jour.")
    else:
        form = SalonSettingsForm(instance=salon)
    return render(request, "settings_salon.html", {"form": form})


# ---------------------------------
# AUTHENTIFICATION
# ---------------------------------
def login_view(request):
    error = None
    salon = SalonSettings.objects.first()
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard') if user.role == 'admin' else redirect('clients_crud')
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect"
    return render(request, "accounts/login.html", {"error": error, "salon": salon})


def logout_view(request):
    logout(request)
    return redirect('login')