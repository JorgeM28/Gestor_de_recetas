from django.shortcuts import render, redirect
from .forms import RecipeForm, CommentForm, UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.models import User
from .models import Recipe, Category, Profile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Repost
from .forms import RepostForm
from .models import Suggestion, Notification
from .forms import SuggestionForm
from django.http import JsonResponse
from django.urls import reverse
from .models import Rating
from .forms import RatingForm
from .models import Favorite  # Añade esto a tus importaciones existentes

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
            return redirect('post:perfil')
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('post:perfil')
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
    recetas_propias = Recipe.objects.filter(author=user, published=True).order_by('-created_at')
    reposts = Repost.objects.filter(reposted_by=user).order_by('-created_at')
    favoritos = Favorite.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'profile_user': user,
        'recetas_propias': recetas_propias,
        'reposts': reposts,
        'favoritos': favoritos,
        'total_recetas_propias': recetas_propias.count(),
        'total_reposts': reposts.count(),
        'total_favoritos': favoritos.count(),
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
            return redirect('post:nueva_receta')
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
        return redirect('post:recetas')
        
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
            return redirect('post:recetas')
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
        return redirect('post:recetas')
        
    if request.method == 'POST':
        receta.delete()
        messages.success(request, 'Receta eliminada correctamente')
        return redirect('post:recetas')
    return render(request, 'post/borrar_receta.html', {'receta': receta})

# Actualiza la función detalle_receta

def detalle_receta(request, recipe_id):
    receta = get_object_or_404(Recipe, id=recipe_id)
    comentarios = receta.comments.all().order_by('-created_at')
    form = CommentForm()
    
    # Verificar si es favorito para el usuario actual
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, recipe=receta).exists()
    
    # Obtener la calificación del usuario si existe
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(recipe=receta, user=request.user).first()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.recipe = receta
            comentario.author = request.user
            comentario.save()
            
            # Crear notificación para el autor de la receta
            if request.user != receta.author:
                Notification.objects.create(
                    recipient=receta.author,
                    sender=request.user,
                    notification_type='comment',
                    content=f"{request.user.username} ha comentado en tu receta '{receta.title}'",
                    related_recipe=receta
                )
            messages.success(request, 'Comentario añadido correctamente')
            return redirect('post:detalle_receta', recipe_id=receta.id)

    tiempo_total = receta.prep_time + receta.cook_time
    
    return render(request, 'post/detalle_receta.html', {
        'receta': receta,
        'comentarios': comentarios,
        'form': form,
        'tiempo_total': tiempo_total,
        'user_rating': user_rating,
        'is_favorite': is_favorite
    })

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión')
            return redirect('post:login')  # Cambiar 'login' por 'post:login'
    else:
        form = UserRegisterForm()
    return render(request, 'post/register.html', {'form': form})

from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse

# Actualiza la función buscar

def buscar(request):
    query = request.GET.get('q', '')
    min_rating = request.GET.get('min_rating', '0')
    difficulty = request.GET.get('difficulty', '')
    categoria_id = request.GET.get('categoria', '')
    
    # Para solicitudes AJAX (búsqueda instantánea) - mantener como está
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Buscar recetas
        recetas = Recipe.objects.filter(
            Q(title__icontains=query) | 
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(published=True).distinct()[:8]
        
        # Buscar usuarios
        usuarios = User.objects.filter(username__icontains=query)[:5]
        
        # Código existente para AJAX - mantener igual
        recetas_data = [{
            'id': r.id,
            'title': r.title,
            'author': r.author.username,
            'image_url': r.recipe_image.url if r.recipe_image else None,
            'url': reverse('post:detalle_receta', args=[r.id])
        } for r in recetas]
        
        usuarios_data = [{
            'username': u.username,
            'image_url': u.profile.profile_image.url if hasattr(u, 'profile') and u.profile.profile_image else None,
            'url': reverse('post:perfil_publico', args=[u.username])
        } for u in usuarios]
        
        return JsonResponse({
            'recetas': recetas_data,
            'usuarios': usuarios_data
        })
    
    # Para la página completa de resultados
    if query:
        recetas = Recipe.objects.filter(
            Q(title__icontains=query) | 
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(published=True).distinct()
        
        usuarios = User.objects.filter(username__icontains=query)
    else:
        recetas = Recipe.objects.filter(published=True)
        usuarios = User.objects.none()
    
    # Asegúrate de que los perfiles estén precargados para evitar consultas N+1
    if usuarios:
        usuarios = usuarios.select_related('profile')
    
    # Aplicar filtro por categoría
    if categoria_id:
        recetas = recetas.filter(category_id=categoria_id)
    
    # Aplicar filtro por dificultad
    if difficulty:
        recetas = recetas.filter(difficulty=difficulty)
    
    # Filtrar por calificación mínima
    if min_rating and min_rating != '0':
        min_rating_value = float(min_rating)
        # Como el filtro de calificación es un cálculo, necesitamos filtrar después
        filtered_recetas = []
        for receta in recetas:
            if receta.average_rating() >= min_rating_value:
                filtered_recetas.append(receta.id)
        
        if filtered_recetas:
            recetas = recetas.filter(id__in=filtered_recetas)
        else:
            recetas = Recipe.objects.none()
    
    # Obtener todas las categorías para los filtros
    categorias = Category.objects.all()
    
    return render(request, 'post/resultados_busqueda.html', {
        'query': query,
        'recetas': recetas,
        'usuarios': usuarios,
        'total_recetas': recetas.count(),
        'total_usuarios': usuarios.count(),
        'categorias': categorias,
        'categoria_seleccionada': categoria_id,
        'min_rating': min_rating,
        'difficulty': difficulty,
        'difficulty_choices': Recipe.DIFFICULTY_CHOICES,
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
                
                # Crear notificación para el autor original
                if recipe.author != request.user:
                    Notification.objects.create(
                        recipient=recipe.author,
                        sender=request.user,
                        notification_type='repost',
                        content=f"{request.user.username} ha reposteado tu receta '{recipe.title}'",
                        related_recipe=recipe
                    )
                    
            return redirect('post:perfil_publico', username=request.user.username)
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

@login_required
def submit_suggestion(request):
    if request.method == 'POST':
        form = SuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.user = request.user
            suggestion.save()
            
            # Crear notificación para administradores
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='suggestion',
                    content=f"{request.user.username} ha enviado una nueva sugerencia",
                    related_suggestion=suggestion
                )
            
            return JsonResponse({'status': 'success', 'message': 'Sugerencia enviada correctamente'})
    
    return JsonResponse({'status': 'error', 'message': 'Error al enviar la sugerencia'})

@login_required
def get_notifications(request):
    try:
        # Primero obtenemos el QuerySet base
        all_notifications = Notification.objects.filter(recipient=request.user)
        
        # Obtenemos el conteo de no leídas antes de aplicar cualquier slice
        unread_count = all_notifications.filter(is_read=False).count()
        
        # Obtenemos las notificaciones recientes para mostrar
        user_notifications = all_notifications.order_by('-created_at')[:5]
        
        notifications_data = []
        for notification in user_notifications:
            notification_data = {
                'id': notification.id,
                'content': notification.content,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'time': notification.created_at.strftime("%d/%m/%Y %H:%M"),
                'sender': notification.sender.username,
            }
            
            if notification.related_recipe:
                notification_data['url'] = reverse('post:detalle_receta', args=[notification.related_recipe.id])
            elif notification.related_suggestion and request.user.is_superuser:
                notification_data['url'] = reverse('post:suggestions_list')  # Añadir el namespace 'post:'
            
            notifications_data.append(notification_data)
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Para depuración en el servidor
        return JsonResponse({
            'error': str(e),
            'notifications': [],
            'unread_count': 0
        }, status=200)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notificación no encontrada'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

@login_required
def suggestions_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('index')
    
    suggestions = Suggestion.objects.all().order_by('-created_at')
    return render(request, 'post/suggestions_list.html', {'suggestions': suggestions})

@login_required
def mark_suggestion_read(request, suggestion_id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'No tienes permiso'})
    
    if request.method == 'POST':
        try:
            suggestion = Suggestion.objects.get(id=suggestion_id)
            suggestion.is_read = True
            suggestion.save()
            return JsonResponse({'status': 'success'})
        except Suggestion.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sugerencia no encontrada'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

@login_required
def rate_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == 'POST':
        # Buscar si ya existe una calificación de este usuario
        rating, created = Rating.objects.get_or_create(
            recipe=recipe,
            user=request.user,
            defaults={'value': request.POST.get('value', 3)}
        )
        
        if not created:
            # Actualizar la calificación existente
            rating.value = request.POST.get('value', rating.value)
            rating.save()
            
        # Crear notificación para el autor de la receta
        if request.user != recipe.author:
            Notification.objects.create(
                recipient=recipe.author,
                sender=request.user,
                notification_type='rating',
                content=f"{request.user.username} ha calificado tu receta '{recipe.title}' con {rating.value} estrellas",
                related_recipe=recipe
            )
        
        messages.success(request, f'Has calificado esta receta con {rating.value} estrellas')
        return redirect('post:detalle_receta', recipe_id=recipe.id)
    
    return redirect('post:detalle_receta', recipe_id=recipe.id)

@login_required
def toggle_favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
    
    if not created:
        # Si ya existía, lo eliminamos
        favorite.delete()
        messages.success(request, 'Receta eliminada de favoritos')
    else:
        # Si es nuevo, notificamos al autor
        if request.user != recipe.author:
            Notification.objects.create(
                recipient=recipe.author,
                sender=request.user,
                notification_type='favorite',
                content=f"{request.user.username} ha añadido tu receta '{recipe.title}' a favoritos",
                related_recipe=recipe
            )
        messages.success(request, 'Receta añadida a favoritos')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'is_favorite': created,
            'total_favorites': recipe.favorited_by.count()
        })
    
    return redirect('post:detalle_receta', recipe_id=recipe.id)

@login_required
def mis_favoritos(request):
    # Obtener los favoritos del usuario actual
    favoritos = Favorite.objects.filter(user=request.user).select_related('recipe', 'recipe__author')
    
    return render(request, 'post/mis_favoritos.html', {
        'favoritos': favoritos,
        'total_favoritos': favoritos.count(),
    })
