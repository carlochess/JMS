from users.models import *

from django.db import transaction



def reset_password(reset_token, reset_code, password):
    try:
        up = UserProfile.objects.get(ResetToken=reset_token)
    except Exception, ex:
        return Response("User profile could not be located", status=400)
    
    try:
        reset_code = int(reset_code)
    except Exception, ex:
        return Response("Reset code should be a number", status=400)
        
    if up.ResetCode == reset_code:
        user = up.user
        with transaction.atomic():
            user.set_password(password)
            user.save()
            
            up.ResetToken = None
            up.ResetCode = None
            up.FailCount = None
            up.save()
                
            auth.update_session_auth_hash(request, user)    
        
        return "Password updated successfully.", 200
        
    else:
        up.FailCount = up.FailCount + 1
        if up.FailCount >= 3:
            up.ResetToken = None
            up.ResetCode = None
            up.FailCount = None
            up.save()
            
            return "The reset code that you entered was incorrect. You have no more tries.", 401
        
        up.save()
        
        remaining_attempts = 3 - up.FailCount
        return "The reset code that you entered was incorrect. Please try again. Attempts remaining: %d" % remaining_attempts, 400


