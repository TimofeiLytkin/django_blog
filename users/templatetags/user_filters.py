from django import template

# Регистрируем наш фильтер.
register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})
