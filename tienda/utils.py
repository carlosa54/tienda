from django.utils import timezone
def jwt_response_payload_handler(token, user, request, *args, **kwargs):
	data = {
		"token": token,
		"user": user.id,
		"orig_iat": timezone.now(),
	}
	return data