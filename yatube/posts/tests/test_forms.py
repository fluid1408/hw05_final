import shutil

from django import forms
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
    TEMP_MEDIA_ROOT,
    TEST_PICTURE_2,
    TEST_SLUG,
    TEST_SLUG1,
    TEST_USER,
    TEST_USER_2,
    OK,
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.user_2 = User.objects.create_user(username=TEST_USER_2)
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
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)
        cls.POST_DETAIL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_COMMENT = reverse("posts:add_comment", args=[cls.post.id])
        cls.REDIRECT_POST_COMMENT = f"{LOGIN}{NEXT}{cls.POST_COMMENT}"
        cls.REDIRECT_POST_EDIT = f"{LOGIN}{NEXT}{cls.POST_EDIT}"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        self.assertEqual(response.status_code, OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            PROFILE,
        )
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, что создалась запись с заданным слагом
        post = Post.objects.get()
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image.name, f'{IMAGE_FOLDER}{form_data["image"].name}'
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            "text": "Второй тестовый пост",
            "group": self.group2.id,
            "image": TEST_PICTURE_2,
        }
        response = self.authorized_client.post(
            self.POST_EDIT, data=form_data, follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(Post.objects.count(), post_count)
        post = response.context["post"]
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group_id, form_data["group"])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image.name, f'{IMAGE_FOLDER}{form_data["image"].name}'
        )

    def test_creat_post_correct_context(self):
        urls = (self.POST_EDIT, POST_CREATE)
        form_fields = {
            "text": forms.CharField,
            "group": forms.fields.ChoiceField,
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                for value, expected in form_fields.items():
                    form_field = response.context["form"].fields.get(value)
                    self.assertIsInstance(form_field, expected)

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

    def test_guest_can_not_create_post_or_comment(self):
        """Неавторизованный пользователь не может создать
        пост или комментарий."""
        Post.objects.all().delete()
        Comment.objects.all().delete()
        cases = (
            (
                Post,
                POST_CREATE,
                REDIRECT_POST_CREATE,
                {
                    "text": "Еще один тестовый пост",
                    "group": self.group2.id,
                    "image": TEST_PICTURE,
                },
            ),
            (
                Comment,
                self.POST_COMMENT,
                self.REDIRECT_POST_COMMENT,
                {"text": "Еще один тестовый комментарий"},
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

    def test_guest_or_non_author_cannot_edit(self):
        """Неавторизованный пользователь и не-автор поста не может
        отредактировать пост."""
        requests = (
            (self.client, "Пост изменен анонимом", self.REDIRECT_POST_EDIT),
            (
                self.authorized_client_2,
                "Пост изменен не-автором",
                self.POST_DETAIL,
            ),
        )
        for client, text, redirect_url in requests:
            with self.subTest(client=client):
                form_data = {
                    "text": text,
                    "group": self.group2,
                    "image": TEST_PICTURE,
                }
                response = client.post(
                    self.POST_EDIT,
                    data=form_data,
                )
                post = Post.objects.get(id=self.post.id)
                self.assertRedirects(response, redirect_url)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)
