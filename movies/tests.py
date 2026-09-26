from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating

User = get_user_model()


class MovieModelTests(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Ciencia ficción")
        self.director = Person.objects.create(
            first_name="Christopher",
            last_name="Nolan",
            role=Person.Role.DIRECTOR,
        )
        self.movie = Movie.objects.create(
            title="Inception",
            release_year=2010,
            synopsis="Robo de secretos a través de los sueños.",
        )
        self.movie.genres.add(self.genre)
        self.movie.people.add(self.director)

    def test_str_includes_title_and_year(self):
        self.assertEqual(str(self.movie), "Inception (2010)")

    def test_absolute_url(self):
        self.assertEqual(
            self.movie.get_absolute_url(),
            reverse("movies:movie_detail", args=[self.movie.pk]),
        )

    def test_average_rating(self):
        Rating.objects.create(movie=self.movie, score=5)
        Rating.objects.create(movie=self.movie, score=4)
        self.assertAlmostEqual(self.movie.get_average_rating(), 4.5)

    def test_directors_property_filters_by_role(self):
        self.assertIn(self.director, self.movie.directors)
        self.assertNotIn(self.director, self.movie.actors)


class EditorsGroupPermissionTests(TestCase):
    """Demuestra que el grupo «Editores» no puede borrar películas."""

    @classmethod
    def setUpTestData(cls):
        cls.movie = Movie.objects.create(title="Alien", release_year=1979)

    def setUp(self):
        self.group = Group.objects.create(name="Editores")
        self.group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="movies",
                codename__in=["add_movie", "change_movie", "view_movie"],
            )
        )
        self.editor = User.objects.create_user(
            username="editor_test",
            password="editor123",
            is_staff=True,
        )
        self.editor.groups.add(self.group)
        self.editor = User.objects.get(pk=self.editor.pk)

    def test_group_has_add_and_change_but_not_delete(self):
        codenames = set(
            self.group.permissions.filter(
                content_type__app_label="movies", content_type__model="movie"
            ).values_list("codename", flat=True)
        )
        self.assertIn("add_movie", codenames)
        self.assertIn("change_movie", codenames)
        self.assertNotIn("delete_movie", codenames)

    def test_editor_can_open_movie_changelist(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:movies_movie_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_editor_can_open_add_movie_form(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:movies_movie_add"))
        self.assertEqual(response.status_code, 200)

    def test_editor_can_open_change_movie_form(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_editor_is_denied_delete_movie_view(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("admin:movies_movie_delete", args=[self.movie.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_delete_changelist_action_does_not_delete(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("admin:movies_movie_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [str(self.movie.pk)],
            },
        )
        self.assertTrue(Movie.objects.filter(pk=self.movie.pk).exists())

    def test_editor_cannot_delete_via_delete_view(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("admin:movies_movie_delete", args=[self.movie.pk]),
            {"post": "yes"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Movie.objects.filter(pk=self.movie.pk).exists())

    def test_editor_cannot_access_other_models_changelist(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:movies_rating_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_audit_fields_are_readonly_in_admin(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        adminform = response.context["adminform"]
        self.assertIn("created_at", adminform.readonly_fields)
        self.assertIn("updated_at", adminform.readonly_fields)
        # No aparecen como campos editables del formulario.
        self.assertNotIn("created_at", adminform.form.fields)
        self.assertNotIn("updated_at", adminform.form.fields)

    def test_delete_action_is_not_available_to_editor(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:movies_movie_changelist"))
        action_form = response.context["action_form"]
        choices = action_form.fields["action"].choices if action_form else []
        codenames = {value for value, _label in choices if value}
        self.assertNotIn("delete_selected", codenames)
        self.assertFalse(codenames)

    def test_ratings_inline_hidden_from_editor_without_rating_permissions(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        models = {
            inline.opts.model.__name__
            for inline in response.context["inline_admin_formsets"]
        }
        self.assertNotIn("Rating", models)

    def test_ratings_inline_is_rendered_for_superuser(self):
        self.client.force_login(
            User.objects.create_superuser(
                username="root", password="root123", email="root@movies.local"
            )
        )
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        models = {
            inline.opts.model.__name__
            for inline in response.context["inline_admin_formsets"]
        }
        self.assertIn("Rating", models)
        self.assertIn("Movie_people", models)

    def test_public_recommendations_open_for_editor(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("movies:recommendations"))
        self.assertEqual(response.status_code, 200)


class PublicViewTests(TestCase):
    """La vista pública no exige autenticación y aplica lógica de negocio."""

    @classmethod
    def setUpTestData(cls):
        cls.scifi = Genre.objects.create(name="Ciencia ficción")
        cls.action = Genre.objects.create(name="Acción")

        cls.best = Movie.objects.create(title="The Matrix", release_year=1999)
        cls.best.genres.add(cls.scifi, cls.action)
        Rating.objects.create(movie=cls.best, score=5)
        Rating.objects.create(movie=cls.best, score=5)

        cls.worst = Movie.objects.create(title="Memento", release_year=2000)
        cls.worst.genres.add(cls.scifi)
        Rating.objects.create(movie=cls.worst, score=3)

        cls.unrated = Movie.objects.create(title="Alien", release_year=1979)

    def test_movie_list_is_public(self):
        response = self.client.get(reverse("movies:movie_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Matrix")
        self.assertContains(response, "Alien")

    def test_movie_list_filters_by_genre(self):
        response = self.client.get(
            reverse("movies:movie_list"), {"genre": self.scifi.pk}
        )
        self.assertEqual(response.status_code, 200)
        titles = [movie.title for movie in response.context["movies"]]
        self.assertIn("The Matrix", titles)
        self.assertIn("Memento", titles)
        self.assertNotIn("Alien", titles)

    def test_movie_list_search(self):
        response = self.client.get(reverse("movies:movie_list"), {"q": "matrix"})
        titles = [movie.title for movie in response.context["movies"]]
        self.assertEqual(titles, ["The Matrix"])

    def test_movie_detail_shows_ratings(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.best.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["ratings"]), 2)
        self.assertAlmostEqual(response.context["movie"].average_rating, 5.0)

    def test_movie_detail_404(self):
        response = self.client.get(reverse("movies:movie_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_recommendations_picks_best_movie_per_genre(self):
        response = self.client.get(reverse("movies:recommendations"))
        self.assertEqual(response.status_code, 200)
        best_per_genre = dict(response.context["best_per_genre"])
        self.assertEqual(best_per_genre[self.scifi].title, "The Matrix")
        self.assertEqual(best_per_genre[self.action].title, "The Matrix")

    def test_recommendations_excludes_unrated_movies(self):
        response = self.client.get(reverse("movies:recommendations"))
        titles = [movie.title for movie in response.context["ranked_movies"]]
        self.assertNotIn("Alien", titles)
        self.assertIn("The Matrix", titles)
        self.assertIn("Memento", titles)

    def test_recommendations_ranking_order(self):
        response = self.client.get(reverse("movies:recommendations"))
        averages = [
            movie.average_rating for movie in response.context["ranked_movies"]
        ]
        self.assertEqual(averages, sorted(averages, reverse=True))

    def test_recommendations_filtered_by_genre(self):
        response = self.client.get(
            reverse("movies:recommendations"), {"genre": self.scifi.pk}
        )
        titles = [movie.title for movie in response.context["ranked_movies"]]
        self.assertEqual(titles, ["The Matrix", "Memento"])

    def test_public_view_available_to_anonymous_user(self):
        response = self.client.get(reverse("movies:recommendations"))
        self.assertNotIn("_auth_user_id", response.context)
