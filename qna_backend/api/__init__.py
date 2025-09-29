"""
API app package for weather Q&A backend.

Avoid importing models/serializers at module import time to prevent
AppRegistryNotReady during Django app population. Import needed symbols
directly from their modules where used.
"""
