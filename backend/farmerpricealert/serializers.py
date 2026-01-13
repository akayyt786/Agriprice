from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        """Validate that email is unique and normalize it"""
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered")
        return email

    def create(self, validated_data):
        # Sanitize username (replace spaces with underscores)
        username = validated_data.get("username", "")
        validated_data["username"] = slugify(username).replace("-", "_")
        
        # Normalize email
        if "email" in validated_data:
            validated_data["email"] = validated_data["email"].lower().strip()

        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)
