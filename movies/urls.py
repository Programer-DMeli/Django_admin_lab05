from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("peliculas/", views.movie_list, name="catalogo"),
    path("peliculas/<int:pk>/", views.movie_detail, name="movie_detail"),
    path("recomendaciones/", views.recommendations, name="recommendations"),
]
