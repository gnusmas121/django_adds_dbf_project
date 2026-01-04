# core/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Извлекает значение из словаря по ключу.
    Используется в шаблоне: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)