from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        # Sanitize username (replace spaces with underscores)
        username = validated_data.get("username", "")
        validated_data["username"] = slugify(username).replace("-", "_")

        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)
