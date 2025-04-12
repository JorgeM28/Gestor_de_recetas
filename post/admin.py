from django.contrib import admin
from .models import Recipe, Category, Comment, Profile, Repost, Rating, Suggestion, Notification

# Registrar los modelos en el admin
admin.site.register(Recipe)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Profile)
admin.site.register(Repost)
admin.site.register(Rating)
admin.site.register(Suggestion)
admin.site.register(Notification)