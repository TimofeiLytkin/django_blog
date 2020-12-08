from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


@cache_page(20, key_prefix="index_page")
def index(request):
    """Функция для формирования главной страницы."""
    post_list = Post.objects.select_related("author", "group").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_index = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page_index, "paginator": paginator, "index": "index"}
    )


def group_post(request, slug):
    """Функция для формирования страницы сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("author", "group").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_group = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page_group, "paginator": paginator},
    )


@login_required()
def post_new(request):
    """Функция проверки и сохранения данных из формы Post."""
    content = [{"heading": "Добавить запись", "button": "Добавить"}]
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new_post.html", {"form": form, "content": content})


def profile(request, username):
    """Функция для формирования страницы пользователя."""
    author = get_object_or_404(User, username=username)
    follower = author.follower.count()
    following = author.following.count()
    post_list = author.posts.select_related("author", "group").all()
    post_count = author.posts.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_author = paginator.get_page(page_number)
    return render(
        request,
        "profile.html",
        {
            "author": author,
            "follower": follower,
            "following": following,
            "page": page_author,
            "post_count": post_count,
            "paginator": paginator,
        }
    )


def post_view(request, username, post_id):
    """Функция для формирования страницы поста."""
    author = get_object_or_404(User, username=username)
    follower = author.follower.count()
    following = author.following.count()
    post = author.posts.get(id=post_id)
    post_count = author.posts.count()
    form = CommentForm()
    items = post.comments.all()
    return render(
        request,
        "post.html",
        {
            "author": author,
            "follower": follower,
            "following": following,
            "post": post,
            "post_count": post_count,
            "form": form,
            "items": items
        }
    )


@login_required()
def post_edit(request, username, post_id):
    """Функция редактирования данных из формы Post."""
    content = [{"heading": "Редактировать запись", "button": "Сохранить"}]
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect("post_view", username=username, post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if form.is_valid():
        form.save()
        return redirect("post_view", username=username, post_id=post_id)
    return render(
        request,
        "new_post.html",
        {"form": form, "post": post, "content": content}
    )


@login_required()
def add_comment(request, username, post_id):
    """Функция для добавления комментария к посту."""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post_view", username=username, post_id=post_id)
    return render(request, "incudes/comments.html", {"form": form, "post": post})


@login_required()
def follow_index(request):
    """Функция для формирования страницы с подписками."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_index = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {"page": page_index, "paginator": paginator, "follow": "follow"}
    )


@login_required()
def profile_follow(request, username):
    """Функция для подписки на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect("profile", username=username)


@ login_required()
def profile_unfollow(request, username):
    """Функция для отписки от автора."""
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=author, user=request.user).exists():
        follow = Follow.objects.get(author=author, user=request.user)
        follow.delete()
    return redirect("profile", username=username)


def year(request):
    """Функция для отображения года на страницах."""
    years = datetime.now().year
    return {"year": years}


def page_not_found(request, exception):
    """Функция для отображения страницы с ошибкой 404."""
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    """Функция для отображения страницы с ошибкой 500."""
    return render(request, "misc/500.html", status=500)
