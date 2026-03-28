from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        """Validate that email is unique and normalize it"""
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered")
        return email

    def to_internal_value(self, data):
        """Sanitize username before validation (e.g., 'Raphael Kerluke' -> 'raphael_kerluke')"""
        if 'username' in data:
            data = data.copy()
            data['username'] = slugify(data['username']).replace("-", "_")
        return super().to_internal_value(data)

    def create(self, validated_data):
        # Normalize email
        if "email" in validated_data:
            validated_data["email"] = validated_data["email"].lower().strip()

        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)
