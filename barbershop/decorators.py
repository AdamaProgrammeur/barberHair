from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Vérifie que l'utilisateur est connecté
            if not request.user.is_authenticated:
                return redirect('login')  # redirige vers la page de login

            # Vérifie si le rôle est dans les rôles autorisés
            if request.user.role not in allowed_roles:
                return redirect('login')  # ou une page "Accès refusé"

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator