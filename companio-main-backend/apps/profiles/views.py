from rest_framework import generics

from .serializers import UserProfileSerializer
from .services import create_profile_for_user


class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return create_profile_for_user(self.request.user)
