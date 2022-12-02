from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
import socket
from TimeSheet.models import ProfileUser
from django.template.defaulttags import register


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,
                                username=cd['username'],
                                password=cd['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse('Authenticated successfully')
            else:
                return HttpResponse('Disabled account')
        else:
            return HttpResponse('Invalid login')
    else:
        user_ip = get_user_ip()
        if user_ip != None:
            login(request, user_ip)
            return HttpResponse('Authenticated successfully')
        else:
            form = LoginForm()
            return render(request, 'account/login.html', {'form': form})

@login_required
def dashboard(request):
    return render(request,'account/dashboard.html',{'section': 'dashboard'})


def get_local_ip():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_local = s.getsockname()[0]
    s.close()

    return ip_local


def get_user_ip():

    ip_local = get_local_ip()
    profil_user = ProfileUser.objects.filter(ip_shop=ip_local).first()

    if profil_user != None:
        return True
    else:
        return False


def ajax_login_user(request):

    if get_user_ip():
        return redirect('table-list')

    return True