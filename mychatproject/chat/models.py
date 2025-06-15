from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ChatMessage(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,blank=True,null=True)
    session_id= models.CharField(max_length=100,null=True,blank=True)
    sender = models.CharField(max_length=10)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] {self.message[:50]}"