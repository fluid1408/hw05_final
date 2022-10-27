import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Post

TEST_SLUG = "test_slug"
TEST_SLUG1 = "test_slug1"
TEST_USER = "test_name"
TEST_USER_2 = "test_name_2"
INDEX = reverse("posts:index")
FOLLOW = reverse("posts:follow_index")
FOLLOW_USER = reverse("posts:profile_follow", args=[TEST_USER])
FOLLOW_USER_2 = reverse("posts:profile_follow", args=[TEST_USER_2])
UNFOLLOW_USER = reverse("posts:profile_unfollow", args=[TEST_USER])
POST_CREATE = reverse("posts:post_create")
GROUP_LIST = reverse("posts:group_list", args=[TEST_SLUG])
GROUP_LIST1 = reverse("posts:group_list", args=[TEST_SLUG1])
NEXT = "?next="
UNEXISTING_PAGE = "/unexisting_page/"
OK = HTTPStatus.OK
REDIRECT = HTTPStatus.FOUND
NOT_FOUND = HTTPStatus.NOT_FOUND
LOGIN = reverse("users:login")
REDIRECT_POST_CREATE = f"{LOGIN}{NEXT}{POST_CREATE}"
REDIRECT_LOGIN_FOLLOW = f"{LOGIN}{NEXT}{FOLLOW_USER}"
REDIRECT_LOGIN_UNFOLLOW = f"{LOGIN}{NEXT}{UNFOLLOW_USER}"
REDIRECT_LOGIN_FOLLOW_INDEX = f"{LOGIN}{NEXT}{FOLLOW}"
PROFILE = reverse("posts:profile", args=[TEST_USER])
IMAGE = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)
TEST_PICTURE = SimpleUploadedFile(
    name="test_pic.png",
    content=IMAGE,
    content_type="image/png",
)
TEST_PICTURE_2 = SimpleUploadedFile(
    name="test_pic_2.png",
    content=IMAGE,
    content_type="image/png",
)
IMAGE_FOLDER = Post._meta.get_field("image").upload_to
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
