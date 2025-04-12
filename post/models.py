from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from PIL import Image
import os
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

# Modelo de la tabla Category
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# Modelo de la tabla Recipe (antes Post)
class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('FACIL', 'Fácil'),
        ('MEDIA', 'Media'),
        ('DIFICIL', 'Difícil'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    ingredients = models.TextField(verbose_name='Ingredientes')
    instructions = models.TextField(verbose_name='Instrucciones')
    prep_time = models.PositiveIntegerField(verbose_name='Tiempo de Preparación (minutos)', default=0)
    cook_time = models.PositiveIntegerField(verbose_name='Tiempo de Cocción (minutos)', default=0)
    servings = models.PositiveIntegerField(verbose_name='Porciones', default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIA', verbose_name='Dificultad')
    recipe_image = models.ImageField(upload_to='recipe_pics/', null=True, blank=True, verbose_name='Imagen de la Receta')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Categoría')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    published = models.BooleanField(default=True, verbose_name='Publicada')

    def __str__(self):
        return self.title
    
    def total_time(self):
        """Retorna el tiempo total de preparación + cocción en minutos"""
        return self.prep_time + self.cook_time

    def resize_image(self):
        if self.recipe_image:
            img = Image.open(self.recipe_image)
            
            # Solo redimensiona si la imagen es más grande que el tamaño máximo deseado
            if img.height > 800 or img.width > 1200:
                output_size = (1200, 800)  # Ancho máximo: 1200px, Alto máximo: 800px
                img.thumbnail(output_size)
                
                # Guardar la imagen redimensionada
                output = BytesIO()
                img_format = 'JPEG' if self.recipe_image.name.lower().endswith('jpg') or self.recipe_image.name.lower().endswith('jpeg') else 'PNG'
                img.save(output, format=img_format, quality=85)
                output.seek(0)
                
                # Reemplazar la imagen original
                self.recipe_image = InMemoryUploadedFile(
                    output, 'ImageField', 
                    os.path.basename(self.recipe_image.name), 
                    f'image/{img_format.lower()}',
                    sys.getsizeof(output), None
                )

    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return round(sum(r.value for r in ratings) / len(ratings), 1)

    def total_ratings(self):
        return self.ratings.count()

# Definir una señal para procesar la imagen antes de guardar
@receiver(pre_save, sender=Recipe)
def process_recipe_image(sender, instance, **kwargs):
    if instance.recipe_image:
        instance.resize_image()

# Renombrar el modelo Comment
class Comment(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="comments", verbose_name='Receta', null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')  
    content = models.TextField(verbose_name='Comentario')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    def __str__(self):
        if self.recipe:
            return f"Comentario en '{self.recipe.title}' por {self.author.username}"
        else:
            return f"Comentario sin receta por {self.author.username}"

# Modelo para el perfil de usuario
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True, verbose_name='Foto de Perfil')
    bio = models.TextField(null=True, blank=True, verbose_name='Biografía')
    
    def __str__(self):
        return f'Perfil de {self.user.username}'

# Crear perfil automáticamente cuando se crea un usuario
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, bio="")  # Añadir bio="" aquí

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        Profile.objects.create(user=instance, bio="")

# Modelo para reposteos de recetas
class Repost(models.Model):
    original_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="reposts", verbose_name='Receta original')
    reposted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reposted_recipes", verbose_name='Reposteado por')
    comment = models.TextField(blank=True, verbose_name='Comentario del repost')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de reposteo')
    
    class Meta:
        unique_together = ('original_recipe', 'reposted_by')  # Prevenir reposteos duplicados
        verbose_name = 'Repost'
        verbose_name_plural = 'Reposts'
        
    def __str__(self):
        return f"{self.reposted_by.username} reposteó {self.original_recipe.title}"

# Modelo para sugerencias (chat)
class Suggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggestions')
    message = models.TextField(verbose_name='Mensaje')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Sugerencia de {self.user.username} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"

# En el modelo Notification, actualiza TYPES

class Notification(models.Model):
    TYPES = (
        ('repost', 'Repost'),
        ('suggestion', 'Nueva sugerencia'),
        ('comment', 'Nuevo comentario'),
        ('rating', 'Nueva calificación'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    content = models.CharField(max_length=255)
    related_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)
    related_suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Notificación para {self.recipient.username}: {self.content}"

# Modelo para calificaciones de recetas
class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ratings", verbose_name='Receta')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    value = models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Calificación')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de calificación')
    
    class Meta:
        unique_together = ('recipe', 'user')  # Un usuario solo puede calificar una vez
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        
    def __str__(self):
        return f"{self.user.username} calificó {self.recipe.title} con {self.value} estrellas"