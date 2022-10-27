from django.test import TestCase

from ..models import User, Group, Post, Comment, Follow


class PostModelTest(TestCase):
    """Создаем тестовый пост и группу."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.user_2 = User.objects.create_user(username="auth_2")
        cls.post = Post.objects.create(
            author=cls.user, text="Новый пост без группы"
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="Тестовый комментарий",
        )
        cls.subscription = Follow.objects.create(
            user=cls.user_2, author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.post), self.post.text[:15])
        self.assertEqual(self.post.text[:15], str(self.post))
        self.assertEqual(self.comment.text[:15], str(self.comment))
        self.assertEqual(
            f"{self.subscription.user.username}-"
            f"{self.subscription.author.username}",
            str(self.subscription),
        )

    def test_models_have_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {"text": "Текст поста", "group": "Группа"}
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value
                )


class GroupModelTest(TestCase):
    """Создаем тестовый пост и группу."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Группа поклонников",
            slug="Граф",
            description="Что-то о группе",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        self.assertEqual(str(group), group.title)
