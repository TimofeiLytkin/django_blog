import io
from unittest import mock
from urllib.parse import urljoin

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.base import ContentFile, File
from django.test import Client, TestCase
from django.urls import reverse

from PIL import Image
from posts.models import Comment, Follow, Group, Post


class TestUser(TestCase):
    def setUp(self):
        self.auth_client = Client()
        self.nonauth_client = Client()

        self.user = User.objects.create_user("user1", "user1@test.com", "12345")
        self.user.save()
        self.auth_client.force_login(self.user)
        self.user_not_found = "max"

        self.text_first = "first text"
        self.text_second = "second text"
        self.text_edit = "edit text"

        self.group = Group.objects.create(
            title="test_group", slug="test_group", description="test_group"
        )

    def url_check(self, user, group, text, post_id, count, image=None):
        cache.clear()
        with self.subTest():
            for url in (
                    reverse("index"),
                    reverse("group_post", kwargs={"slug": group.slug}),
                    reverse("profile", kwargs={"username": user}),
                    reverse(
                        "post_view",
                        kwargs={"username": user, "post_id": post_id}
                    )
            ):
                response = self.auth_client.get(url)
                if 'paginator' in response.context:
                    current_post = response.context["paginator"].object_list[0]
                    self.assertEqual(
                        len(response.context["paginator"].object_list), count
                    )
                else:
                    current_post = response.context["post"]
                    self.assertEqual(response.context["post_count"], count)
                self.assertEqual(current_post.author, user)
                self.assertEqual(current_post.group, group)
                self.assertEqual(current_post.text, text)
                if image:
                    self.assertEqual(current_post.image, image)

    def test_profile_page(self):
        response = self.auth_client.get(
            reverse("profile", kwargs={"username": self.user})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(
            response.context["author"].username, self.user.username
        )

    def test_auth_client_create_post(self):
        self.auth_client.post(
            reverse("post_new"),
            data={"text": self.text_first, "group": self.group.id}
        )
        self.auth_client.get(
            reverse("post_new"),
            data={"text": self.text_second, "group": self.group.id}
        )

        posts = Post.objects.all()

        self.assertIn(self.text_first, [post.text for post in posts])
        self.assertNotIn(self.text_second, [post.text for post in posts])

        self.url_check(
            user=self.user,
            group=self.group,
            text=self.text_first,
            post_id=posts.first().id,
            count=posts.count()
        )

    def test_nonauth_client_create_post(self):
        self.nonauth_client.post(
            reverse("post_new"),
            data={"text": self.text_first, "group": self.group.id}
        )
        self.nonauth_client.get(
            reverse("post_new"),
            data={"text": self.text_second, "group": self.group.id},
        )

        posts = Post.objects.all()
        url = urljoin(reverse("login"), "?next=/new/")
        response = self.nonauth_client.get(reverse("post_new"))

        self.assertNotIn(self.text_first, [post.text for post in posts])
        self.assertNotIn(self.text_second, [post.text for post in posts])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

    def test_auth_client_edit_post(self):
        post = Post.objects.create(
            text=self.text_first, author=self.user, group=self.group
        )
        group = Group.objects.create(
            title="edit_group", slug="edit_group", description="edit_group"
        )
        self.auth_client.post(
            reverse(
                "post_edit",
                kwargs={"post_id": post.id, "username": self.user}
            ),
            data={"text": self.text_edit, "group": group.id}
        )
        self.auth_client.get(
            reverse(
                "post_edit",
                kwargs={"post_id": post.id, "username": self.user}
            ),
            data={"text": self.text_second, "group": group.id}
        )

        posts_edit = Post.objects.all()

        self.assertIn(self.text_edit, [post.text for post in posts_edit])
        self.assertNotIn(self.text_second, [post.text for post in posts_edit])

        self.url_check(
            user=self.user,
            group=group,
            text=self.text_edit,
            post_id=posts_edit.first().id,
            count=posts_edit.count()
        )

    def test_error_404(self):
        response = self.auth_client.get(
            reverse("profile", kwargs={"username": self.user_not_found})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "misc/404.html")

    def test_auth_client_add_comment(self):
        post = Post.objects.create(
            text=self.text_first, author=self.user, group=self.group
        )
        self.auth_client.post(
            reverse(
                "add_comment",
                kwargs={"username": self.user, "post_id": post.id}
            ),
            data={"text": self.text_first}
        )
        self.auth_client.get(
            reverse(
                "add_comment",
                kwargs={"username": self.user, "post_id": post.id}
            ),
            data={"text": self.text_second}
        )

        comments = Comment.objects.all()

        self.assertIn(self.text_first, [com.text for com in comments])
        self.assertNotIn(self.text_second, [com.text for com in comments])

    def test_nonauth_client_add_comment(self):
        post = Post.objects.create(
            text=self.text_first, author=self.user, group=self.group
        )
        self.nonauth_client.post(
            reverse(
                "add_comment",
                kwargs={"username": self.user, "post_id": post.id}
            ),
            data={"text": self.text_first}
        )
        self.nonauth_client.get(
            reverse(
                "add_comment",
                kwargs={"username": self.user, "post_id": post.id}
            ),
            data={"text": self.text_second}
        )

        comments = Comment.objects.all()

        self.assertNotIn(self.text_first, [com.text for com in comments])
        self.assertNotIn(self.text_second, [com.text for com in comments])

    def test_loading_image(self):
        buffer = io.BytesIO()
        img = Image.new("RGB", (500, 500), (0, 0, 0))
        img.save(buffer, format="jpeg")
        buffer.seek(0)
        image = ContentFile(buffer.read(), name='test.jpeg')
        request_post = self.auth_client.post(
            reverse("post_new"),
            data={
                "author": self.user,
                "text": self.text_first,
                "group": self.group.id,
                "image": image
            }
        )
        request_get = self.auth_client.get(
            reverse("post_new"),
            data={
                "author": self.user,
                "text": self.text_second,
                "group": self.group.id,
                "image": image
            }
        )

        posts = Post.objects.all()

        self.assertEqual(posts.count(), 1)
        self.assertEqual(request_post.status_code, 302)
        self.assertEqual(request_get.status_code, 200)

        self.url_check(
            user=self.user,
            group=self.group,
            text=self.text_first,
            post_id=posts.first().id,
            count=posts.count(),
            image=posts.first().image
        )

    def test_loading_nonimage(self):
        file = mock.MagicMock(spec=File, name="test.txt")
        request_post = self.auth_client.post(
            reverse("post_new"),
            data={
                "author": self.user,
                "text": self.text_first,
                "group": self.group.id,
                "image": file
            }
        )
        request_get = self.auth_client.get(
            reverse("post_new"),
            data={
                "author": self.user,
                "text": self.text_second,
                "group": self.group.id,
                "image": file
            }
        )

        posts = Post.objects.all()

        text_error = (f"Загрузите правильное изображение. Файл, который вы "
                      f"загрузили, поврежден или не является изображением.")

        self.assertEqual(posts.count(), 0)
        self.assertEqual(request_post.status_code, 200)
        self.assertEqual(request_get.status_code, 200)
        self.assertFormError(
            request_post, form="form", field="image", errors=text_error
        )

    def test_cache(self):
        cache.clear()
        with self.assertNumQueries(3):
            response = self.auth_client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)
            response = self.auth_client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)

        self.auth_client.post(
                reverse("post_new"),
                data={"text": self.text_first, "group": self.group.id}
        )
        response = self.auth_client.get(reverse("index"))
        self.assertNotContains(response, self.text_first)

    def follow_to_author(self):
        self.author = User.objects.create_user(
            "user2", "user2@test.com", "12345"
        )
        self.auth_client.get(
            reverse(
                "profile_follow",
                kwargs={"username": self.author.username}
            )
        )

    def test_auth_follow_to_author(self):
        self.follow_to_author()
        follow = Follow.objects.all()
        self.assertEqual(len(follow), 1)
        self.assertEqual(follow.first().author, self.author)
        self.assertEqual(follow.first().user, self.user)

    def test_auth_unfollow_to_author(self):
        self.follow_to_author()
        self.auth_client.get(
            reverse(
                "profile_unfollow",
                kwargs={"username": self.author.username}
            )
        )
        follow = Follow.objects.all()
        self.assertEqual(len(follow), 0)

    def test_nonauth_nonfollow_to_author(self):
        author = User.objects.create_user("user2", "user2@test.com", "12345")
        self.nonauth_client.get(
            reverse("profile_follow", kwargs={"username": author.username}),
        )
        follow = Follow.objects.all()
        self.assertEqual(len(follow), 0)

    def test_append_post_in_follow_index(self):
        author = User.objects.create_user("user2", "user2@test.com", "12345")
        post = Post.objects.create(text=self.text_first, author=author)
        self.auth_client.get(
            reverse("profile_follow", kwargs={"username": author.username}),
        )
        response = self.auth_client.get(reverse("follow_index"))
        current_post = response.context["paginator"].object_list[0]
        self.assertEqual(len(response.context["paginator"].object_list), 1)
        self.assertEqual(current_post.author, author)
        self.assertEqual(current_post.text, post.text)
