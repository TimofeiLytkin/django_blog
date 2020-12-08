from django.contrib import admin

from posts.models import Comment, Follow, Group, Post


class CommentAdmin(admin.ModelAdmin):
    """Модель для отображения полей комментария в админке."""

    list_display = ("pk", "post", "author", "text", "created")
    search_fields = ("text",)
    empty_value_display = "-пусто-"


class FollowAdmin(admin.ModelAdmin):
    """Модель для отображения полей подписки в админке."""

    list_display = ("pk", "user", "author")
    search_fields = ("user",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    """Модель для отображения полей сообщества в админке."""

    list_display = ("pk", "title", "slug", "description")
    search_fields = ("description",)
    empty_value_display = "-пусто-"


class PostAdmin(admin.ModelAdmin):
    """Модель для отображения полей постов в админке."""

    list_display = ("pk", "text", "pub_date", "author")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
