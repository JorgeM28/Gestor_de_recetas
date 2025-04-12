from django.shortcuts import render, redirect
from .forms import RecipeForm, CommentForm, UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.models import User
from .models import Recipe, Category, Profile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Repost
from .forms import RepostForm

def index(request):
    recetas_recientes = Recipe.objects.filter(published=True).order_by('-created_at')[:6]  # Últimas 6 recetas
    return render(request, 'post/index.html', {'recetas_recientes': recetas_recientes})

@login_required
def categorias(request):
    categorias = Category.objects.all()
    categoria_id = request.GET.get('categoria')  # Capturar la categoría seleccionada
    recetas = Recipe.objects.filter(published=True).order_by('-created_at')
    
    if categoria_id:
        categoria = get_object_or_404(Category, id=categoria_id)
        recetas = recetas.filter(category=categoria)        

    return render(request, 'post/categorias.html', {
        'categorias': categorias,
        'recetas': recetas,
        'categoria_seleccionada': categoria_id
    })

@login_required
def recetas(request):
    if request.user.is_superuser or request.user.is_staff:
        recetas = Recipe.objects.all().order_by('-created_at')  # Muestra todas las recetas
    else:
        recetas = Recipe.objects.filter(author=request.user).order_by('-created_at')  # Muestra solo las del usuario actual
    return render(request, 'post/recetas.html', {'recetas': recetas})

@login_required
def perfil(request):
    try:
        profile = request.user.profile
    except:
        profile = Profile.objects.create(user=request.user, bio="")
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if 'delete_image' in request.POST:
            profile.profile_image = None
            profile.save()
            messages.success(request, 'Foto de perfil eliminada correctamente')
            return redirect('perfil')
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'post/perfil_usuario.html', context)

def perfil_publico(request, username):
    user = get_object_or_404(User, username=username)
    
    # Recetas creadas por el usuario
    recetas_propias = Recipe.objects.filter(author=user, published=True).order_by('-created_at')
    
    # Recetas reposteadas por el usuario
    reposts = Repost.objects.filter(reposted_by=user).order_by('-created_at')
    
    # Obtener estadísticas del usuario
    total_recetas_propias = recetas_propias.count()
    total_reposts = reposts.count()
    categorias_usadas = Category.objects.filter(recipe__author=user, recipe__published=True).distinct()
    
    context = {
        'profile_user': user,
        'recetas_propias': recetas_propias,
        'reposts': reposts,
        'total_recetas_propias': total_recetas_propias,
        'total_reposts': total_reposts,
        'total_recetas': total_recetas_propias + total_reposts,
        'categorias_usadas': categorias_usadas,
    }
    
    return render(request, 'post/perfil_publico.html', context)

@login_required
def nueva_receta(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.author = request.user
            receta.save()
            messages.success(request, 'Receta creada correctamente')
            return redirect('recetas')
    else:
        form = RecipeForm()
    return render(request, 'post/nueva_receta.html', {'form': form})

@login_required
def editar_receta(request, recipe_id):
    receta = get_object_or_404(Recipe, id=recipe_id)
    
    # Reescribir la lógica de permisos de forma más clara
    es_propietario = (request.user == receta.author)
    es_admin = (request.user.is_superuser or request.user.is_staff)
    
    if not (es_propietario or es_admin):
        messages.error(request, 'No tienes permiso para editar esta receta.')
        return redirect('recetas')
        
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=receta)
        if form.is_valid():
            # Guardar sin cambiar el autor original
            receta_actualizada = form.save(commit=False)
            # Mantener el autor original si un admin está editando
            if not es_propietario and es_admin:
                receta_actualizada.author = receta.author
            receta_actualizada.save()
            messages.success(request, 'Receta actualizada correctamente')
            return redirect('recetas')
    else:
        form = RecipeForm(instance=receta)
    
    return render(request, 'post/editar_receta.html', {
        'form': form, 
        'receta': receta,
        'es_propietario': es_propietario
    })

@login_required
def eliminar_receta(request, recipe_id):
    receta = get_object_or_404(Recipe, id=recipe_id)
    
    # Reescribir la lógica de permisos de forma más clara
    es_propietario = (request.user == receta.author)
    es_admin = (request.user.is_superuser or request.user.is_staff)
    
    if not (es_propietario or es_admin):
        messages.error(request, 'No tienes permiso para eliminar esta receta.')
        return redirect('recetas')
        
    if request.method == 'POST':
        receta.delete()
        messages.success(request, 'Receta eliminada correctamente')
        return redirect('recetas')
    return render(request, 'post/borrar_receta.html', {'receta': receta})

def detalle_receta(request, recipe_id):
    receta = get_object_or_404(Recipe, id=recipe_id)
    comentarios = receta.comments.all().order_by('-created_at')
    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.recipe = receta
            comentario.author = request.user
            comentario.save()
            messages.success(request, 'Comentario añadido correctamente')
            return redirect('detalle_receta', recipe_id=receta.id)

    tiempo_total = receta.prep_time + receta.cook_time
    
    return render(request, 'post/detalle_receta.html', {
        'receta': receta,
        'comentarios': comentarios,
        'form': form,
        'tiempo_total': tiempo_total
    })

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'post/register.html', {'form': form})

from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse

def buscar(request):
    query = request.GET.get('q', '')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if query:
        # Buscar recetas
        recetas = Recipe.objects.filter(
            Q(title__icontains=query) | 
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(published=True).distinct()[:8]
        
        # Buscar usuarios
        usuarios = User.objects.filter(username__icontains=query)[:5]
    else:
        recetas = Recipe.objects.none()
        usuarios = User.objects.none()
    
    # Si es una solicitud AJAX, devolver resultados en formato JSON
    if is_ajax:
        recetas_data = [{
            'id': r.id,
            'title': r.title,
            'author': r.author.username,
            'image_url': r.recipe_image.url if r.recipe_image else None,
            'url': reverse('detalle_receta', args=[r.id])
        } for r in recetas]
        
        usuarios_data = [{
            'username': u.username,
            'image_url': u.profile.profile_image.url if hasattr(u, 'profile') and u.profile.profile_image else None,
            'url': reverse('perfil_publico', args=[u.username])
        } for u in usuarios]
        
        return JsonResponse({
            'recetas': recetas_data,
            'usuarios': usuarios_data
        })
    
    # Si es una solicitud normal, renderizar plantilla completa
    return render(request, 'post/resultados_busqueda.html', {
        'query': query,
        'recetas': recetas,
        'usuarios': usuarios,
        'total_recetas': recetas.count(),
        'total_usuarios': usuarios.count()
    })

@login_required
def repost_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Verificar si ya existe un repost del usuario actual
    existing_repost = Repost.objects.filter(original_recipe=recipe, reposted_by=request.user).first()
    
    if request.method == 'POST':
        form = RepostForm(request.POST)
        if form.is_valid():
            if existing_repost:
                # Actualizar el repost existente
                existing_repost.comment = form.cleaned_data['comment']
                existing_repost.save()
                messages.success(request, 'Repost actualizado correctamente')
            else:
                # Crear nuevo repost
                repost = form.save(commit=False)
                repost.original_recipe = recipe
                repost.reposted_by = request.user
                repost.save()
                messages.success(request, 'Receta reposteada correctamente')
            return redirect('perfil_publico', username=request.user.username)
    else:
        initial_data = {}
        if existing_repost:
            initial_data = {'comment': existing_repost.comment}
        form = RepostForm(initial=initial_data)
    
    return render(request, 'post/repost_recipe.html', {
        'form': form,
        'recipe': recipe,
        'existing_repost': existing_repost
    })
