from .models import SalonSettings

def salon_settings(request):
    salon = SalonSettings.objects.first()
    return {'salon': salon}