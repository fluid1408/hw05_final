from django.core.paginator import Paginator
from yatube.settings import POSTS_ON_PAGE


def paginator_posts(post_list, request):
    return Paginator(post_list, POSTS_ON_PAGE).get_page(
        request.GET.get("page")
    )
