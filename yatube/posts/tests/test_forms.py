import shutil
import tempfile

from django import forms
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User
from .constants import (
    IMAGE_FOLDER,
    LOGIN,
    NEXT,
    POST_CREATE,
    PROFILE,
    REDIRECT_POST_CREATE,
    TEST_PICTURE,
    TEST_PICTURE_2,
    TEST_SLUG,
    TEST_SLUG1,
    TEST_USER,
)

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=TEST_SLUG,
            description="Тестовое описание группы",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст",
            group=cls.group,
        )
        cls.group2 = Group.objects.create(
            title="Группа",
            slug=TEST_SLUG1,
            description="Тестовое описание",
        )
        cls.POST_DETAIL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_COMMENT = reverse("posts:add_comment", args=[cls.post.id])
        cls.REDIRECT_POST_COMMENT = f"{LOGIN}{NEXT}{cls.POST_COMMENT}"
        cls.REDIRECT_POST_EDIT = f"{LOGIN}{NEXT}{cls.POST_EDIT}"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
            "image": TEST_PICTURE,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            POST_CREATE, data=form_data, follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            PROFILE,
        )
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, что создалась запись с заданным слагом
        post = Post.objects.get()
        self.assertEqual(post.group_id, form_data["group"])
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image.name, f'{IMAGE_FOLDER}{form_data["image"].name}'
        )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE)
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post(self):
        post = Post.objects.create(
            text="Тестовый текст", group=self.group, author=self.user
        )
        form_data = {
            "text": "Новый текст",
            "group": self.group2.id,
            "image": TEST_PICTURE_2,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=[post.id]),
            data=form_data,
            follow=True,
        )
        post.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
        ),
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(self.post.author, post.author)
        self.assertEqual(
            post.image.name, f'{IMAGE_FOLDER}{form_data["image"].name}'
        )

    def test_guest_can_not_create_post_or_comment(self):
        Post.objects.all().delete()
        Comment.objects.all().delete()
        cases = (
            (
                Post,
                POST_CREATE,
                REDIRECT_POST_CREATE,
                {
                    "text": "Еще тестовый пост",
                    "group": self.group2.id,
                    "image": TEST_PICTURE,
                },
            ),
            (
                Comment,
                self.POST_COMMENT,
                self.REDIRECT_POST_COMMENT,
                {"text": "Еще тестовый комментарий"},
            ),
        )
        for (
            obj,
            url,
            redirect_url,
            form_data,
        ) in cases:
            with self.subTest(url=url):
                response = self.client.post(url, data=form_data, follow=True)
                self.assertRedirects(response, redirect_url)
                self.assertEqual(len(obj.objects.all()), 0)

    def test_create_comment(self):
        Comment.objects.all().delete()
        form_data = {"text": "Новый комментарий"}
        response = self.authorized_client.post(
            self.POST_COMMENT, data=form_data, follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(len(Comment.objects.all()), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
