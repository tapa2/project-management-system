from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect('projects:list')
    return render(request, 'core/home.html')
