from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

GENRES = ["Acción", "Aventura", "Ciencia ficción", "Suspenso"]

PEOPLE = [
    ("Keanu", "Reeves", Person.Role.ACTOR),
    ("Carrie-Anne", "Moss", Person.Role.ACTOR),
    ("Laurence", "Fishburne", Person.Role.ACTOR),
    ("Lana", "Wachowski", Person.Role.DIRECTOR),
    ("Lilly", "Wachowski", Person.Role.DIRECTOR),
    ("Tom", "Hanks", Person.Role.ACTOR),
    ("Robert", "Zemeckis", Person.Role.DIRECTOR),
    ("Edward", "Norton", Person.Role.ACTOR),
    ("Helena", "Bonham Carter", Person.Role.ACTOR),
    ("Guy", "Pearce", Person.Role.ACTOR),
    ("Christian", "Bale", Person.Role.ACTOR),
    ("Christopher", "Nolan", Person.Role.DIRECTOR),
    ("Leonardo", "DiCaprio", Person.Role.ACTOR),
    ("Sigourney", "Weaver", Person.Role.ACTOR),
    ("Ridley", "Scott", Person.Role.DIRECTOR),
    ("Bruce", "Willis", Person.Role.ACTOR),
    ("Steven", "Spielberg", Person.Role.DIRECTOR),
    ("Sam", "Neill", Person.Role.ACTOR),
    ("Peter", "Falk", Person.Role.ACTOR),
]

# (título, año, sinopsis, géneros, [(nombre, apellido)], [(puntuación, comentario)])
MOVIES = [
    (
        "The Matrix",
        1999,
        "Un programador descubre que la realidad es una simulación.",
        ["Ciencia ficción", "Acción"],
        [("Keanu", "Reeves"), ("Carrie-Anne", "Moss"), ("Lilly", "Wachowski")],
        [
            (5, "Una obra maestra del cine de ciencia ficción."),
            (5, "La acción y la filosofía se combinan perfectamente."),
        ],
    ),
    (
        "Forrest Gump",
        1994,
        "Un hombre sencillo vive una vida extraordinaria por accidente.",
        ["Aventura", "Acción"],
        [("Tom", "Hanks"), ("Robert", "Zemeckis")],
        [(5, "Emotiva y perfecta para cualquier momento.")],
    ),
    (
        "Fight Club",
        1999,
        "Un oficinista y un vendedor de jabón forman un club de peleas clandestino.",
        ["Suspenso", "Acción"],
        [("Edward", "Norton"), ("Helena", "Bonham Carter")],
        [(4, "Gran guion con un final inesperado.")],
    ),
    (
        "Memento",
        2000,
        "Un hombre con amnesia investiga el asesinato de su esposa.",
        ["Suspenso", "Ciencia ficción"],
        [("Guy", "Pearce"), ("Christopher", "Nolan")],
        [(5, "La estructura narrativa es lo mejor de Nolan.")],
    ),
    (
        "Inception",
        2010,
        "Un ladrón roba secretos a través de los sueños.",
        ["Ciencia ficción", "Acción", "Suspenso"],
        [("Leonardo", "DiCaprio"), ("Christopher", "Nolan")],
        [
            (5, "La mejor película de Nolan para mi gusto."),
            (4, "Perfecta para ver en un domingo por la tarde."),
        ],
    ),
    (
        "The Dark Knight",
        2008,
        "Batman se enfrenta al Joker en Ciudad Gótica.",
        ["Acción", "Suspenso"],
        [("Christian", "Bale"), ("Christopher", "Nolan")],
        [(5, "El Joker es un antagonista memorable.")],
    ),
    (
        "Alien",
        1979,
        "La tripulación de una nave encuentra una forma de vida hostil.",
        ["Ciencia ficción", "Suspenso"],
        [("Sigourney", "Weaver"), ("Ridley", "Scott")],
        [(4, "Tensión y diseño de producción excelentes.")],
    ),
    (
        "Die Hard",
        1988,
        "Un policia atrapado en un rascacielos.",
        ["Acción", "Suspenso"],
        [("Bruce", "Willis")],
        [],
    ),
    (
        "The Lord of the Rings: The Fellowship of the Ring",
        2001,
        "Un hobbit parte en un viaje para destruir el Anillo Único.",
        ["Aventura", "Acción"],
        [],
        [],
    ),
    (
        "Jurassic Park",
        1993,
        "Un parque de dinosaurios queda fuera de control tras un sabotaje.",
        ["Aventura", "Acción"],
        [("Sam", "Neill"), ("Steven", "Spielberg")],
        [(4, "Aventura pura, muy divertida.")],
    ),
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo: 4 géneros, 10 películas y valoraciones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Borra los datos existentes antes de cargar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            Rating.objects.all().delete()
            Movie.objects.all().delete()
            Person.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write("Datos anteriores eliminados.")

        genres = {name: Genre.objects.get_or_create(name=name)[0] for name in GENRES}

        people = {
            (first, last): Person.objects.get_or_create(
                first_name=first,
                last_name=last,
                defaults={"role": role},
            )[0]
            for first, last, role in PEOPLE
        }

        created_movies = 0
        created_ratings = 0

        for title, year, synopsis, genre_names, cast, ratings in MOVIES:
            movie, created = Movie.objects.get_or_create(
                title=title,
                release_year=year,
                defaults={"synopsis": synopsis},
            )
            if created:
                created_movies += 1

            movie.genres.set([genres[name] for name in genre_names])
            movie.people.set(
                [people[person] for person in cast if person in people]
            )

            for score, comment in ratings:
                _, is_new = Rating.objects.get_or_create(
                    movie=movie,
                    score=score,
                    comment=comment,
                )
                if is_new:
                    created_ratings += 1

        rated = Movie.objects.filter(ratings__isnull=False).distinct().count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {Genre.objects.count()} géneros, "
                f"{Person.objects.count()} personas, "
                f"{Movie.objects.count()} películas, "
                f"{Rating.objects.count()} valoraciones en {rated} películas."
            )
        )
        self.stdout.write(
            f"Nuevas películas: {created_movies} | Nuevas valoraciones: {created_ratings}"
        )
