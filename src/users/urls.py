from django.conf.urls import patterns, url
from users import views

urlpatterns = patterns('users.views',
    
    url(r'login/?', views.Login.as_view()), 
    url(r'logout/?', views.Logout.as_view()),  
    url(r'profile/?', views.Profile.as_view()), 
    url(r'password/?', views.Password.as_view()),
    url(r'', views.Register.as_view()),    
)
