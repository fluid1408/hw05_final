from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import POSTS_ON_PAGE

from ..models import Follow, Group, Post, User
from .constants import (
    FOLLOW,
    FOLLOW_USER_2,
    GROUP_LIST,
    GROUP_LIST1,
    INDEX,
    PROFILE,
    TEST_PICTURE,
    TEST_SLUG,
    TEST_SLUG1,
    TEST_USER,
    TEST_USER_2,
    UNFOLLOW_USER,
)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USER)
        cls.user_2 = User.objects.create_user(username=TEST_USER_2)
        Follow.objects.create(user=cls.user_2, author=cls.user)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title="Test Group",
            slug=TEST_SLUG,
            description="test description of the group",
        )
        cls.another_group = Group.objects.create(
            slug=TEST_SLUG1,
            title="Вторая тестовая группа",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.user,
            group=cls.group,
            image=TEST_PICTURE,
        )
        cls.POST_DETAIL = reverse("posts:post_detail", args=[cls.post.id])

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.pk, self.post.pk)
            self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(INDEX)
        self.assertEqual(len(response.context["page_obj"]), 1)
        context = response.context.get("page_obj")[0]
        self.check_post_info(context)

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_LIST)
        self.assertEqual(len(response.context["page_obj"]), 1)
        context = response.context.get("page_obj")[0]
        group = response.context["group"]
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.check_post_info(context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(PROFILE)
        self.assertEqual(len(response.context["page_obj"]), 1)
        context = response.context.get("page_obj")[0]
        self.assertEqual(response.context["author"], self.user)
        self.check_post_info(context)

    def test_detail_page_show_correct_context(self):
        response = self.authorized_client.get(self.POST_DETAIL)
        self.check_post_info(response.context["post"])

    def test_the_post_not_appear_templates_not_intended(self):
        urls = (GROUP_LIST1, FOLLOW)
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertNotIn(self.post, response.context["page_obj"])

    def test_cache_index_page(self):
        response_1 = self.authorized_client.get(INDEX)
        Post.objects.all().delete()
        response_2 = self.authorized_client.get(INDEX)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(INDEX)
        self.assertNotEqual(response_1.content, response_3.content)

    def test_follow_page(self):
        Post.objects.all().delete()
        follow_count = Follow.objects.count()
        self.authorized_client.get(FOLLOW_USER_2)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.user_2).exists()
        )

    def test_unfollow_page(self):
        Post.objects.all().delete()
        follow_count = Follow.objects.count()
        self.authorized_client2.get(UNFOLLOW_USER)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(user=self.user_2, author=self.user).exists()
        )

    def test_post_on_group_list(self):
        response = self.authorized_client.get(GROUP_LIST)
        group = response.context["group"]
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.id, self.group.id)

    def test_pages_contain_num_posts(self):
        cache.clear()
        Post.objects.all().delete()
        self.posts = Post.objects.bulk_create(
            Post(
                author=self.user,
                group=self.group,
                text=f"Тестовый пост {i}",
            )
            for i in range(POSTS_ON_PAGE + 1)
        )
        test = [
            [INDEX, POSTS_ON_PAGE],
            [GROUP_LIST, POSTS_ON_PAGE],
            [PROFILE, POSTS_ON_PAGE],
            [FOLLOW, POSTS_ON_PAGE],
            [f"{INDEX}?page=2", 1],
            [f"{GROUP_LIST}?page=2", 1],
            [f"{PROFILE}?page=2", 1],
            [f"{FOLLOW}?page=2", 1],
        ]
        for url, value in test:
            with self.subTest(page=url):
                response = self.authorized_client2.get(url)
                self.assertEqual(len(response.context["page_obj"]), value)
