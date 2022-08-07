from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200, unique_for_date="published_at")
    body = models.TextField()
    published_at = models.DateField()
