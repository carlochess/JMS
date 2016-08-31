from users.serializers import *
from users.Utilities.Enums import *
from users.models import *

from datetime import datetime
import json, helpers

from django.db import transaction
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.http import QueryDict
from django.conf import settings

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response



class Login(APIView):
	
	def post(self, request):		
		username = request.POST['username']
		password = request.POST['password']
		
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:				
				login(request, user)				
				serializer = UserSerializer(user)
				return Response(serializer.data)
			else:
				return Response(status=status.HTTP_403_FORBIDDEN)
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)


class Logout(APIView):
	permission_classes = (IsAuthenticated,)
	
	def get(self, request):
		logout(request)
		return Response(200)


class Register(APIView):
	
	def post(self, request):
		serialized = UserSerializer(data=request.DATA)
		if serialized.is_valid():
			user = User.objects.create_user(
			    serialized.init_data['email'], 
			    email=serialized.init_data['email'], 
			    password=serialized.init_data['password'],
			    first_name=serialized.init_data['first_name'],
			    last_name=serialized.init_data['last_name']
			)
			return Response(serialized.data, status=status.HTTP_201_CREATED)
		else:
			return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


class Profile(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		"""
		Get user details
		"""
		u = User.objects.get(id=request.user.id)
		up, created = UserProfile.objects.get_or_create(user = u)
		
		serializer = UserProfileSerializer(up)
		return Response(serializer.data)
	
	def put(self, request):
		"""
		Update user details
		"""
		put = QueryDict(request.body)
		
		u = User.objects.get(id=request.user.id)
		up, created = UserProfile.objects.get_or_create(user = u)
		
		u.first_name = put.get('first_name')
		u.last_name = put.get('last_name')
		u.email = put.get('email')
		u.save()
		
		up.Field = put.get('field')
		up.Company = put.get('company')
		
		country = put.get('country')
		if(country == ""):
			up.Country_id = None
		else:
			up.Country_id = country
		
		up.DoB = put.get('dob')
		up.save()
		
		serializer = UserProfileSerializer(up)
		return Response(serializer.data)
	
	
class Password(APIView):
	permission_classes = (IsAuthenticated,)
	
	def put(self, request):
		"""
		Update password
		"""
		put = QueryDict(request.body)
		
		user = request.user
		
		if user.check_password(put.get('old_password')):
			user.set_password(put.get('new_password'))
			user.save()			
			return Response(status=200)
		else:
			return Response(status=401)
	
	
class Reset(APIView):
    
    def post(self, request):
        email = request.body;
        try:
            user = User.objects.get(email=email)
        except Exception, ex:
            return Response("User profile could not be found", status=400)
        
        reset_token = random.randint(10000, 9999999)
        reset_code = random.randint(10000, 9999999)
        
        with transaction.atomic():
            profile = user.userprofile
            profile.FailCount = 0
            profile.ResetToken = reset_token
            profile.ResetCode = reset_code
            profile.save()
            
            name = "%s %s" % (user.first_name, user.last_name)
            
            #Send email with reset code
            email = EmailMessage('Reset password for Primo', 
                "Dear %s,\n\nYou requested a password reset for your JMS account. " % name +
                "Enter the reset code below into the box provided at https://jms.rubi.ru.ac.za/account/reset?token=%d.\n\nReset code: %d" % (reset_token, reset_code) +
                "\n\nIf you did not make this request, you can simply ignore this e-mail.\n\nKind regards,\n" +
                "The JMS team",
                settings.EMAIL_HOST_USER, #from
                [user.email] #to 
            )
            email.send()
        
        return Response()
    
    def put(self, request):
        
        data = json.loads(request.body)
        message, status = helpers.reset_password(data["reset_token"], 
            data["reset_code"], data['password'])
        
        return Response(message, status=status)


