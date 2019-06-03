from django.urls import path
from . import views

app_name = 'welcome'
urlpatterns = [
    path('home/', views.home, name='home'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('clear_data/', views.clear_data, name='clear_data'),
    # path('user_login/', views.user_login, name='user_login'),
]
