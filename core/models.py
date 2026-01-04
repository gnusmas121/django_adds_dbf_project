# core/models.py
from django.db import models
from django.contrib.auth.models import User

class DBFUpload(models.Model):
    """
    Модель для отслеживания загрузок DBF-файлов.
    """
    filename = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255, unique=True) # Имя таблицы в БД
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.filename} -> {self.table_name}"


class ExcelUpload(models.Model):
    """
    Модель для отслеживания загрузок Excel-файлов.
    """
    filename = models.CharField(max_length=255) # Имя загруженного файла
    table_name = models.CharField(max_length=255) # Имя таблицы в БД (НЕ уникальное для Excel)
    uploaded_at = models.DateTimeField(auto_now_add=True) # Время загрузки
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE) # Кто загрузил

    def __str__(self):
        return f"{self.filename} -> {self.table_name}"


from django.db import models
from django.contrib.auth.models import User

# ... (остальные модели) ...

class TableTemplate(models.Model):
    """
    Модель для шаблона таблицы.
    Подходит для любой таблицы в базе.
    """
    table_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Имя таблицы в базе данных (например, 'my_table_name')."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Пользователь, который создал шаблон."
    )

    def __str__(self):
        return f"Шаблон для {self.table_name}"

    class Meta:
        app_label = 'core'
        # permissions = (
        #     ("can_upload_dbf", "Может загружать DBF файлы"),
        # )

class TableTemplateFieldConfig(models.Model):
    """
    Модель для хранения конфигурации отдельного поля в шаблоне таблицы.
    """
    TEMPLATE_TYPE_CHOICES = [
        ('search', 'Поиск'),
        ('result', 'Вывод'),
    ]

    table_template = models.ForeignKey(
        TableTemplate,
        on_delete=models.CASCADE,
        related_name='field_configs' # Позволяет получить все настройки полей для шаблона
    )
    field_name = models.CharField(
        max_length=255,
        help_text="Имя столбца в базе данных (например, 'last_name')."
    )
    field_label = models.CharField(
        max_length=255,
        help_text="Подпись поля (например, 'ФАМИЛИЯ')."
    )
    template_type = models.CharField(
        max_length=10,
        choices=TEMPLATE_TYPE_CHOICES,
        help_text="Тип шаблона: для поиска или для вывода."
    )
    # Порядок поля (если нужно сохранить порядок)
    order = models.PositiveIntegerField(default=0, help_text="Порядок поля в шаблоне.")

    class Meta:
        app_label = 'core'
        unique_together = ('table_template', 'field_name', 'template_type') # Один столбец одного типа на шаблон
        ordering = ['template_type', 'order'] # Сортировка по типу и порядку

    def __str__(self):
        return f"{self.table_template.table_name} - {self.field_name} ({self.template_type}) -> {self.field_label}"