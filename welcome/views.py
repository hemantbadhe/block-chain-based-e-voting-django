import subprocess

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from Crypto.PublicKey import ECC
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from bbevoting_project.settings import SEND_EMAIL
from simulation.models import *
import os


@login_required(login_url='/')
def home(request):
    context = {
        'tx': settings.N_TRANSACTIONS,
        'bl': settings.N_BLOCKS,
    }
    return render(request, 'welcome/home.html', context)


def sign_up(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.create(first_name=first_name, last_name=last_name, username=email, email=email)
        user_obj.set_password(password)
        # user_obj.save(co)

        # user_details_obj = User.objects.create(user=user_obj)

        # Generate Private key
        name = "{}_{}".format(user_obj.first_name, user_obj.last_name)
        key = ECC.generate(curve='P-256')
        private_key = key.export_key(format='PEM')

        f = open('utils/private_' + name + '.pem', 'wt')
        f.write(key.export_key(format='PEM'))
        f.close()

        print('**********************')
        print(private_key)
        print('**********************')

        # Generate Public Key

        f = open('utils/public_' + name + '.pem', 'wt')
        f.write(key.public_key().export_key(format='PEM'))
        f.close()

        user_obj.public_key = key.public_key().export_key(format='PEM')
        user_obj.save()

        if SEND_EMAIL:
            try:
                subject = 'Welcome to E Voting System'
                html_message = render_to_string('welcome/private_key.html',
                                                {'username': user_obj.email, "private_key": private_key})
                plain_message = strip_tags(html_message)
                from_email = settings.EMAIL_HOST_USER

                to = user_obj.email

                mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
            except Exception as e:
                messages.warning(request, 'Invalid Email!')
        messages.success(request, 'User Sign Up success..!')
        return redirect('/')

    elif request.method == "GET":
        return render(request, 'welcome/sign_up.html')


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/home')
        else:
            messages.warning(request, "Invalid login")
            return render(request, 'welcome/login.html')
    elif request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/home')
        return render(request, 'welcome/login.html')


@login_required(login_url='/')
def user_logout(request):
    logout(request)
    return redirect('/')


from django.db import connection


@login_required(login_url='/')
def clear_data(request):
    Vote.objects.all().delete()
    VoteBackup.objects.all().delete()
    Block.objects.all().delete()

    cursor = connection.cursor()
    cursor.execute('ALTER TABLE simulation_vote AUTO_INCREMENT = 1')
    cursor.execute('ALTER TABLE simulation_votebackup AUTO_INCREMENT = 1')
    cursor.execute('ALTER TABLE simulation_block AUTO_INCREMENT = 1')
    cursor.fetchall()
    cursor.close()
    return redirect('welcome:home')
