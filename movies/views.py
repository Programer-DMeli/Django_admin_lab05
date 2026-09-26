from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Genre, Movie


def movie_list(request):
    """Catálogo público: sólo lectura, sin permisos de admin."""
    movies = (
        Movie.objects.annotate(
            average_rating=Avg("ratings__score"),
            rating_count=Count("ratings", distinct=True),
        )
        .prefetch_related("genres")
        .order_by("-average_rating", "title")
    )

    genre_slug = request.GET.get("genre")
    selected_genre = None
    if genre_slug:
        selected_genre = get_object_or_404(Genre, pk=genre_slug)
        movies = movies.filter(genres=selected_genre)

    search = request.GET.get("q", "").strip()
    if search:
        movies = movies.filter(
            Q(title__icontains=search) | Q(synopsis__icontains=search)
        )

    context = {
        "movies": list(movies),
        "genres": Genre.objects.annotate(movie_count=Count("movies")),
        "selected_genre": selected_genre,
        "search": search,
    }
    return render(request, "movies/movie_list.html", context)


def movie_detail(request, pk):
    movie = get_object_or_404(
        Movie.objects.annotate(
            average_rating=Avg("ratings__score"),
            rating_count=Count("ratings", distinct=True),
        ).prefetch_related("genres", "people"),
        pk=pk,
    )

    related_ids = movie.genres.values_list("id", flat=True)
    related = (
        Movie.objects.filter(genres__in=related_ids)
        .exclude(pk=movie.pk)
        .annotate(average_rating=Avg("ratings__score"))
        .distinct()
        .order_by("-average_rating", "title")[:5]
    )

    context = {
        "movie": movie,
        "ratings": movie.ratings.all(),
        "related_movies": related,
    }
    return render(request, "movies/movie_detail.html", context)


def recommendations(request):
    """
    Lógica de negocio pública: para cada género se elige la película mejor
    valorada (media de puntuaciones). No usa permisos del admin: cualquiera
    puede consultar esta vista.
    """
    genre_pk = request.GET.get("genre")
    selected_genre = None
    if genre_pk:
        selected_genre = get_object_or_404(Genre, pk=genre_pk)

    rated_movies = (
        Movie.objects.annotate(
            average_rating=Avg("ratings__score"),
            rating_count=Count("ratings", distinct=True),
        )
        .filter(ratings__isnull=False)
        .prefetch_related("genres")
        .order_by("-average_rating", "title")
    )

    if selected_genre:
        rated_movies = rated_movies.filter(genres=selected_genre)

    ranked = list(rated_movies)

    if selected_genre:
        best_per_genre = []
    else:
        # `ranked` viene ordenado de mayor a menor media, así que la primera
        # película que aparece para un género es la mejor valorada de ese
        # género. Una película puede ganar en varios géneros a la vez.
        seen = set()
        best_per_genre = []
        for movie in ranked:
            for genre in movie.genres.all():
                if genre.pk not in seen:
                    seen.add(genre.pk)
                    best_per_genre.append((genre, movie))

    context = {
        "best_per_genre": best_per_genre,
        "ranked_movies": ranked,
        "genres": Genre.objects.annotate(movie_count=Count("movies")),
        "selected_genre": selected_genre,
    }
    return render(request, "movies/recommendations.html", context)
