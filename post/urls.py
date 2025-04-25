from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Esta línea es OBLIGATORIA para usar el namespace
app_name = 'post'

urlpatterns = [
    path('', views.index, name='index'),
    path('buscar/', views.buscar, name='buscar'),
    path('categorias/', views.categorias, name='categorias'),
    path('recetas/', views.recetas, name='recetas'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('recetas/nueva/', views.nueva_receta, name='nueva_receta'),
    path('recetas/editar/<int:recipe_id>/', views.editar_receta, name='editar_receta'),
    path('recetas/eliminar/<int:recipe_id>/', views.eliminar_receta, name='eliminar_receta'),
    path('receta/<int:recipe_id>/', views.detalle_receta, name='detalle_receta'),
    path('receta/<int:recipe_id>/repost/', views.repost_recipe, name='repost_recipe'),
    path('receta/<int:recipe_id>/calificar/', views.rate_recipe, name='rate_recipe'),
    path('register/', views.register, name='register'),
    path('usuario/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('sugerencia/enviar/', views.submit_suggestion, name='submit_suggestion'),
    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('sugerencias/', views.suggestions_list, name='suggestions_list'),
    path('sugerencias/marcar-leida/<int:suggestion_id>/', views.mark_suggestion_read, name='mark_suggestion_read'),
    path('submit_suggestion/', views.submit_suggestion, name='submit_suggestion'),
    path('mark_suggestion_read/<int:suggestion_id>/', views.mark_suggestion_read, name='mark_suggestion_read'),
    path('suggestions/', views.suggestions_list, name='suggestions_list'),
    path('login/', auth_views.LoginView.as_view(template_name='post/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]