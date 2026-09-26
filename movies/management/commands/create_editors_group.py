from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

GROUP_NAME = "Editores"
TEST_USERNAME = "editor1"
TEST_PASSWORD = "editor123"
TEST_EMAIL = "editor1@movies.local"

# El grupo puede crear y modificar películas, pero NO borrarlas.
ALLOWED_PERMISSIONS = [
    ("add_movie", "Añadir película"),
    ("change_movie", "Modificar película"),
    ("view_movie", "Ver película"),
]

#(app_label, codename) --> NO se otorgan deliberadamente
FORBIDDEN_PERMISSIONS = [
    ("delete_movie", "Borrar película"),
]


class Command(BaseCommand):
    help = (
        "Crea el grupo «Editores» con permisos de añadir y modificar películas "
        "(sin permiso de borrado) y un usuario de prueba miembro del grupo."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", default=TEST_USERNAME)
        parser.add_argument("--email", default=TEST_EMAIL)
        parser.add_argument("--password", default=TEST_PASSWORD)
        parser.add_argument(
            "--with-view",
            action="store_true",
            help="Incluye también el permiso de solo lectura (view_movie).",
        )

    def handle(self, *args, **options):
        movie_ct = ContentType.objects.get(app_label="movies", model="movie")

        group, _created = Group.objects.get_or_create(name=GROUP_NAME)

        codenames = [codename for codename, _label in ALLOWED_PERMISSIONS]
        if not options["with_view"] and "view_movie" in codenames:
            codenames.remove("view_movie")

        granted = Permission.objects.filter(
            content_type=movie_ct,
            codename__in=codenames,
        )
        group.permissions.set(granted)

        for codename, _label in FORBIDDEN_PERMISSIONS:
            group.permissions.filter(codename=codename).delete()

        User = get_user_model()
        user, user_created = User.objects.get_or_create(
            username=options["username"],
            defaults={"email": options["email"], "is_staff": True},
        )
        user.is_staff = True
        user.is_superuser = False
        user.set_password(options["password"])
        user.save()
        user.groups.add(group)

        self.stdout.write(self.style.SUCCESS(f"Grupo «{group.name}» listo."))
        for permission in group.permissions.select_related("content_type"):
            self.stdout.write(
                f"  + {permission.content_type.app_label}.{permission.codename} "
                f"({permission.name})"
            )
        for codename, label in FORBIDDEN_PERMISSIONS:
            self.stdout.write(self.style.WARNING(f"  - {codename} ({label}) NO otorgado"))

        state = "creado" if user_created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario «{user.username}» {state} | is_staff={user.is_staff} "
                f"| is_superuser={user.is_superuser} | grupos="
                f"{list(user.groups.values_list('name', flat=True))}"
            )
        )
        self.stdout.write(f"Credenciales: {user.username} / {options['password']}")
