from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator_posts


@cache_page(20)
def index(request):
    template = "posts/index.html"
    posts = Post.objects.all()
    context = {
        "page_obj": paginator_posts(posts, request),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        "group": group,
        "page_obj": paginator_posts(posts, request),
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    context = {
        "author": author,
        "page_obj": paginator_posts(author.posts.all(), request),
        "following": request.user.is_authenticated
        and request.user != author
        and Follow.objects.filter(author=author, user=request.user).exists(),
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(Post, id=post_id)
    context = {
        "post": post,
        "form": CommentForm(),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, "posts/create_post.html", {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", username=post.author)


@login_required
def post_edit(request, pk):
    template = "posts/create_post.html"
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id=pk)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post.save()
        return redirect("posts:post_detail", post_id=pk)
    context = {"form": form, "is_edit": True}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    tempalate = "posts/follow.html"
    context = {
        "page_obj": paginator_posts(
            Post.objects.filter(author__following__user=request.user), request
        ),
    }
    return render(request, tempalate, context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if follow_author != request.user and (
        not request.user.follower.filter(author=follow_author).exists()
    ):
        Follow.objects.create(user=request.user, author=follow_author)
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, author__username=username, user=request.user
    ).delete()
    return redirect("posts:profile", username=username)
