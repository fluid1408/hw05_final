from django.core.paginator import Paginator


def paginator_posts(post_list, request):
    return Paginator(post_list, 10).get_page(request.GET.get("page"))
