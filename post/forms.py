from django import forms
from .models import Recipe, Comment, Profile, Repost
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'ingredients', 'instructions', 'prep_time', 'cook_time', 
                 'servings', 'difficulty', 'recipe_image', 'category', 'published']
        labels = {
            'title': 'Título',
            'ingredients': 'Ingredientes',
            'instructions': 'Instrucciones',
            'prep_time': 'Tiempo de Preparación (minutos)',
            'cook_time': 'Tiempo de Cocción (minutos)',
            'servings': 'Porciones',
            'difficulty': 'Dificultad',
            'recipe_image': 'Imagen de la Receta',
            'category': 'Categoría',
            'published': '¿Publicar ahora?',
        }
        widgets = {
            'title': forms.TextInput(attrs={'id': 'title', 'class': 'form-control'}),
            'ingredients': forms.Textarea(attrs={'id': 'ingredients', 'rows': 5, 'placeholder': 'Escribe los ingredientes, uno por línea...', 'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'id': 'instructions', 'rows': 8, 'placeholder': 'Escribe las instrucciones paso por paso...', 'class': 'form-control'}),
            'prep_time': forms.NumberInput(attrs={'id': 'prep_time', 'min': 0, 'class': 'form-control'}),
            'cook_time': forms.NumberInput(attrs={'id': 'cook_time', 'min': 0, 'class': 'form-control'}),
            'servings': forms.NumberInput(attrs={'id': 'servings', 'min': 1, 'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'id': 'difficulty', 'class': 'form-control'}),
            'category': forms.Select(attrs={'id': 'category', 'class': 'form-control'}),
            'published': forms.CheckboxInput(attrs={'id': 'published'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe un comentario...', 'class': 'form-control'})
        }

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'Nombre de usuario',
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']
        labels = {
            'profile_image': 'Foto de perfil',
            'bio': 'Biografía',
        }

class RepostForm(forms.ModelForm):
    class Meta:
        model = Repost
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'placeholder': 'Añade un comentario a este repost...', 'rows': 3}),
        }