from django.db import models

# Create your models here.
class Singer(models.Model):
    # info
    id = models.CharField(max_length=30, primary_key=True, unique=True)
    name = models.CharField(max_length=20)
    url = models.URLField()
    image = models.ImageField(upload_to="singer/", blank=True)
    image_url = models.URLField()
    info = models.JSONField(default=list)
    info_text = models.CharField(max_length=10000)
    # func
    def __str__(self) -> str:
        return self.name


class Song(models.Model):
    # info
    id = models.CharField(max_length=30, primary_key=True, unique=True)
    name = models.CharField(max_length=20)
    url = models.URLField()
    image = models.ImageField(upload_to="song/", blank=True)
    image_url = models.URLField()
    singers = models.ManyToManyField(Singer, related_name="songs")
    lyrics = models.JSONField(default=list)
    lyrics_text = models.CharField(max_length=10000)
    # func
    def __str__(self) -> str:
        return self.name


class Comment(models.Model):
    # info
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    text = models.CharField()
    time = models.DateTimeField()
    # func
    def __str__(self) -> str:
        return self.text[:10] + "..."