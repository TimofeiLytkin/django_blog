from django.forms import ModelForm
from posts.models import Comment, Post


class PostForm(ModelForm):
    """Класс форма для создания новых постов."""

    class Meta:
        model = Post
        fields = ("group", "text", "image")
        help_texts = {
            "text": "Даже Чехов боялся чистого листа.\n Просто начни."
        }


class CommentForm(ModelForm):
    """Класс форма для создания новых комментария к посту."""

    class Meta:
        model = Comment
        fields = ("text",)
        help_texts = {"text": "Введите текст комментария."}
