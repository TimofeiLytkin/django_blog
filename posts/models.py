from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель для создания сообщества."""

    title = models.CharField(max_length=200, verbose_name="Имя")
    slug = models.SlugField(unique=True, verbose_name="Адрес")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title

    class Meta:

        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class Post(models.Model):
    """Модель для создания постов."""

    text = models.TextField(verbose_name="Текст")
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="Группа"
    )
    image = models.ImageField(
        upload_to='posts/', blank=True, null=True, verbose_name="Изображение"
    )

    def __str__(self):
        return self.text

    class Meta:

        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ("-pub_date",)


class Comment(models.Model):
    """Модель для создания комментариев."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст")
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации")

    def __str__(self):
        return self.text

    class Meta:

        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Follow(models.Model):
    """Модель для создания подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Пользователь"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор"
    )

    class Meta:

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("user", "author")
