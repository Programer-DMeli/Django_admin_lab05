from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(
        verbose_name="Nombre",
        max_length=50,
        unique=True,
    )

    class Meta:
        verbose_name = "Género"
        verbose_name_plural = "Géneros"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    class Role(models.TextChoices):
        ACTOR = "actor", "Actor"
        DIRECTOR = "director", "Director"
        WRITER = "writer", "Guionista"
        PRODUCER = "producer", "Productor"

    first_name = models.CharField(verbose_name="Nombre", max_length=100)
    last_name = models.CharField(verbose_name="Apellido", max_length=100)
    role = models.CharField(
        verbose_name="Rol",
        max_length=20,
        choices=Role.choices,
        default=Role.ACTOR,
    )
    bio = models.TextField(verbose_name="Biografía", blank=True)
    photo = models.ImageField(
        verbose_name="Foto",
        upload_to="personas/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(verbose_name="Título", max_length=200)
    release_year = models.PositiveSmallIntegerField(
        verbose_name="Año de estreno",
        validators=[
            MinValueValidator(1888),
            MaxValueValidator(2100),
        ],
    )
    poster = models.ImageField(
        verbose_name="Póster",
        upload_to="posters/",
        blank=True,
        null=True,
    )
    synopsis = models.TextField(verbose_name="Sinopsis", blank=True)
    genres = models.ManyToManyField(
        Genre,
        verbose_name="Géneros",
        related_name="movies",
        blank=True,
    )
    people = models.ManyToManyField(
        Person,
        verbose_name="Reparto y equipo",
        related_name="movies",
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name="Fecha de creación",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="Fecha de modificación",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Película"
        verbose_name_plural = "Películas"
        ordering = ["-release_year", "title"]

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def get_absolute_url(self):
        return reverse("movies:movie_detail", kwargs={"pk": self.pk})

    def get_average_rating(self):
        """Media de las valoraciones. No usar como property: las vistas
        anotan el mismo nombre con Avg("ratings__score") y la anotación
        debe poder sobrescribir el atributo de la instancia."""
        return self.ratings.aggregate(models.Avg("score"))["score__avg"]

    @property
    def genres_names(self):
        return ", ".join(self.genres.values_list("name", flat=True))

    genres_names.fget.short_description = "Géneros"

    @property
    def people_names(self):
        return ", ".join(str(person) for person in self.people.all())

    @property
    def directors(self):
        return self.people.filter(role=Person.Role.DIRECTOR)

    @property
    def actors(self):
        return self.people.filter(role=Person.Role.ACTOR)


class Rating(models.Model):
    class RatingScale(models.IntegerChoices):
        ONE_STAR = 1, "1 estrella"
        TWO_STARS = 2, "2 estrellas"
        THREE_STARS = 3, "3 estrellas"
        FOUR_STARS = 4, "4 estrellas"
        FIVE_STARS = 5, "5 estrellas"

    movie = models.ForeignKey(
        Movie,
        verbose_name="Película",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    score = models.PositiveSmallIntegerField(
        verbose_name="Puntuación",
        choices=RatingScale.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(verbose_name="Comentario", blank=True)
    created_at = models.DateTimeField(
        verbose_name="Fecha de creación",
        default=timezone.now,
    )

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movie.title} - {self.score}/5"
