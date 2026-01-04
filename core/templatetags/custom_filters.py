# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Позволяет получить значение из словаря в шаблоне по ключу.
    Usage: {{ dictionary|get_item:key }}
    """
    # Этот фильтр не подходит напрямую к QuerySet из existing_configs
    # Нужно преобразовать его в словарь в представлении или использовать другой подход.
    # Пока уберем его из шаблона и будем использовать цикл.
    return dictionary.get(key)

@register.filter
def get_type(configs, field_and_type):
    """
    Фильтр для получения настройки по имени поля и типу.
    Usage: (не подходит напрямую к списку, нужно использовать в цикле)
    """
    # Сложно использовать напрямую, лучше обойтись циклом в шаблоне.
    # Мы создадим словарь в представлении.
    pass