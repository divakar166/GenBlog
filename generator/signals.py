from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BlogPost
import requests
import os

@receiver(post_save, sender=BlogPost)
def generate_thumbnail(sender, instance, created, **kwargs):
    if created and not instance.thumbnail:
        limewire_api_endpoint = "https://api.limewire.com/api/image/generation"
        payload = {
            "prompt": f"Thumbnail for blog on topic : {instance.title}",
            "aspect_ratio": "1:1"
        }
        headers = {
            "Content-Type": "application/json",
            "X-Api-Version": "v1",
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ.get('IMAGE_GEN_API_KEY')}"
        }
        response = requests.post(limewire_api_endpoint, json=payload, headers=headers)
        data = response.json()
        thumbnail_url = data['data'][0]['asset_url']
        if thumbnail_url:
            instance.thumbnail = thumbnail_url
            instance.save()
