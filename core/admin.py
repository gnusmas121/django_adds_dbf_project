# core/admin.py
from django.contrib import admin
from django import forms
from django.db import models
from .models import DBFUpload, ExcelUpload, TableTemplate, TableTemplateFieldConfig # Импортируем новые модели

# ... (регистрация DBFUpload, ExcelUpload) ...

class TableTemplateFieldConfigInlineForm(forms.ModelForm):
    """
    Форма для одной строки в Inline (одно поле).
    """
    # field_name = forms.CharField(widget=forms.TextInput(attrs={'size': '20'})) # Опционально: размер поля
    # field_label = forms.CharField(widget=forms.TextInput(attrs={'size': '20'})) # Опционально: размер поля
    pass # Пока без изменений, можно добавить валидацию

class TableTemplateFieldConfigInline(admin.TabularInline): # Используем TabularInline для табличного вида
    model = TableTemplateFieldConfig
    form = TableTemplateFieldConfigInlineForm
    extra = 1 # Количество пустых строк для добавления
    # min_num = 0 # Минимальное количество (опционально)
    # max_num = 50 # Максимальное количество (опционально)

    # Фильтры для выбора полей (если бы у нас был способ получить список столбцов таблицы заранее)
    # forms.CharField не позволяет легко задать список вариантов без динамического изменения формы
    # Пока оставим как есть, пользователь вводит имя столбца вручную, но мы можем добавить валидацию.

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Увеличим размер полей ввода
        if db_field.name == 'field_name' or db_field.name == 'field_label':
            kwargs['widget'] = forms.TextInput(attrs={'size': '30'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

class TableTemplateAdminForm(forms.ModelForm):
    """
    Форма для админки TableTemplate.
    """
    class Meta:
        model = TableTemplate
        fields = '__all__'

@admin.register(TableTemplate)
class TableTemplateAdmin(admin.ModelAdmin):
    form = TableTemplateAdminForm
    inlines = [TableTemplateFieldConfigInline] # Добавляем Inline
    list_display = ('table_name', 'created_at', 'created_by')
    search_fields = ('table_name',)
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('table_name',)
        }),
        ('Автор', {
            'fields': ('created_by',),
            'classes': ('collapse',) # Свернуть
        }),
        ('Создано', {
            'fields': ('created_at',),
            'classes': ('collapse',) # Свернуть
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id and not change: # Если это новая запись
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # Опционально: добавить валидацию в форме или в модели
    # def clean(self):
    #     cleaned_data = super().clean()
    #     table_name = cleaned_data.get("table_name")
    #     # Проверить, существуют ли указанные field_name в таблице table_name
    #     # Это сложнее сделать в админке, т.к. доступ к связанной модели Inline ограничен
    #     # Лучше проверять при сохранении в представлении или модели
    #     return cleaned_data

# ... (если есть другие модели) ...