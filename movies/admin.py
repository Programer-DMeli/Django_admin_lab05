from django.contrib import admin
from django.utils.html import format_html

from .models import Genre, Movie, Person, Rating


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "movie_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Nº de películas", ordering="movie_count")
    def movie_count(self, obj):
        return obj.movies.count()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "movie_count")
    list_filter = ("role",)
    search_fields = ("first_name", "last_name")
    ordering = ("last_name", "first_name")
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "role")}),
        ("Datos extra", {"classes": ("collapse",), "fields": ("bio", "photo")}),
    )

    @admin.display(description="Nº de películas", ordering="movie_count")
    def movie_count(self, obj):
        return obj.movies.count()


class RatingInline(admin.TabularInline):
    """Valoraciones editables dentro del formulario de Movie."""

    model = Rating
    extra = 1
    fields = ("score", "comment", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    verbose_name = "Valoración"
    verbose_name_plural = "Valoraciones"


class PersonMovieInline(admin.TabularInline):
    """Reparto y equipo: edición de la tabla intermedia Movie <-> Person."""

    model = Movie.people.through
    extra = 1
    fields = ("person", "person_role")
    readonly_fields = ("person_role",)
    autocomplete_fields = ("person",)
    verbose_name = "Persona"
    verbose_name_plural = "Reparto y equipo"

    @admin.display(description="Rol")
    def person_role(self, obj):
        if not obj.person_id:
            return ""
        return obj.person.get_role_display()


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "poster_thumbnail",
        "title",
        "release_year",
        "genres_names",
        "average_rating",
        "rating_count",
        "created_at",
    )
    list_filter = ("genres", "release_year", "created_at")
    search_fields = ("title", "synopsis", "people__first_name", "people__last_name")
    list_editable = ("release_year",)
    list_per_page = 20
    date_hierarchy = "created_at"
    filter_horizontal = ("genres", "people")
    inlines = (RatingInline, PersonMovieInline)
    readonly_fields = ("created_at", "updated_at", "average_rating")
    fieldsets = (
        (None, {"fields": ("title", "release_year", "poster", "synopsis")}),
        ("Clasificación", {"fields": ("genres", "people")}),
        (
            "Auditoría (solo lectura)",
            {
                "classes": ("collapse",),
                "fields": ("average_rating", "created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Póster")
    def poster_thumbnail(self, obj):
        if not obj.poster:
            return "—"
        return format_html(
            '<img src="{}" style="height:60px;border-radius:4px;" />',
            obj.poster.url,
        )

    @admin.display(description="Puntuación media", ordering="average_rating")
    def average_rating(self, obj):
        average = obj.get_average_rating()
        return f"{average:.2f} / 5" if average is not None else "Sin valorar"

    @admin.display(description="Nº de valoraciones")
    def rating_count(self, obj):
        return obj.ratings.count()


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("movie", "score", "comment_preview", "created_at")
    list_filter = ("score", "movie__genres", "created_at")
    search_fields = ("movie__title", "comment")
    list_select_related = ("movie",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("movie",)
    readonly_fields = ("created_at",)
    list_per_page = 25
    fieldsets = (
        (None, {"fields": ("movie", "score", "comment")}),
        ("Auditoría", {"classes": ("collapse",), "fields": ("created_at",)}),
    )

    @admin.display(description="Comentario")
    def comment_preview(self, obj):
        text = obj.comment or "—"
        return text[:60] + "…" if len(text) > 60 else text
