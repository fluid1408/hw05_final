from django.contrib.auth import get_user
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User
from .constants import (
    GROUP_LIST,
    INDEX,
    LOGIN,
    NEXT,
    NOT_FOUND,
    OK,
    POST_CREATE,
    PROFILE,
    REDIRECT,
    REDIRECT_POST_CREATE,
    TEST_SLUG,
    TEST_USER,
    TEST_USER_2,
    UNEXISTING_PAGE,
)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.user_2 = User.objects.create_user(username=TEST_USER_2)
        cls.group = Group.objects.create(
            slug=TEST_SLUG,
            title="Тестовая группа",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text="Тестовый пост",
        )
        cls.POST_DETAIL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT = reverse("posts:post_edit", args=[cls.post.id])
        cls.REDIRECT_LOGIN_POST_EDIT = f"{LOGIN}{NEXT}{cls.POST_EDIT}"
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another_author = Client()
        cls.another_author.force_login(cls.user_2)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            INDEX: "posts/index.html",
            GROUP_LIST: "posts/group_list.html",
            PROFILE: "posts/profile.html",
            self.POST_DETAIL: "posts/post_detail.html",
            POST_CREATE: "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(self.author.get(address), template)

    def test_URLs_users_acces(self):
        pages_response = [
            [INDEX, self.client, OK],
            [GROUP_LIST, self.client, OK],
            [PROFILE, self.client, OK],
            [self.POST_DETAIL, self.client, OK],
            [self.POST_EDIT, self.client, REDIRECT],
            [POST_CREATE, self.client, REDIRECT],
            [UNEXISTING_PAGE, self.client, NOT_FOUND],
            [self.POST_EDIT, self.author, OK],
            [POST_CREATE, self.author, OK],
            [self.POST_EDIT, self.another_author, REDIRECT],
        ]
        for address, client, return_code in pages_response:
            with self.subTest(address=address, client=get_user(client).username):
                self.assertEqual(client.get(address).status_code, return_code)

    def test_urls_redirect_guest_client(self):
        pages_redirect = [
            [POST_CREATE, self.client, REDIRECT_POST_CREATE],
            [self.POST_EDIT, self.client, self.REDIRECT_LOGIN_POST_EDIT],
            [self.POST_EDIT, self.another_author, self.POST_DETAIL],
        ]
        """Редирект неавторизованного пользователя"""
        for url, client, redirect in pages_redirect:
            with self.subTest(url=url, client=get_user(client).username):
                self.assertRedirects(client.get(url), redirect)
