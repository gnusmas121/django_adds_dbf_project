# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import connection
import dbfread
import tempfile
import os
import re # Для проверки имени таблицы

# Импортируем модель, если используем (для логирования)
# from .models import DBFUpload # Убедитесь, что модель DBFUpload создана в models.py, если вы её используете

# Вспомогательная функция для проверки, является ли пользователь суперпользователем
def is_superuser(user):
    return user.is_superuser

# Вспомогательная функция для проверки, может ли пользователь использовать поиск
def can_search(user):
    # Проверяем, является ли пользователь суперпользователем ИЛИ состоит в группе 'can_search' ИЛИ is_staff
    # is_staff устанавливается через AUTH_LDAP_USER_FLAGS_BY_GROUP, если пользователь в нужной группе ADDS
    return user.is_superuser or user.groups.filter(name='can_search').exists() or user.is_staff

@login_required # Пользователь должен быть аутентифицирован
@user_passes_test(can_search) # Пользователь должен пройти проверку can_search
def search(request):
    results = []
    available_tables = []

    # --- Получаем список таблиц ---
    # Вариант 2: Прямо из PostgreSQL (без модели, более универсально)
    with connection.cursor() as cursor:
        # Получаем имена пользовательских таблиц (не системных, не Django)
        # Это исключает таблицы, начинающиеся с 'pg_', 'sql_', 'django_', 'auth_', 'contenttype'
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename NOT LIKE 'pg_%'
              AND tablename NOT LIKE 'sql_%'
              AND tablename NOT LIKE 'django_%'
              AND tablename NOT LIKE 'auth_%'
              AND tablename NOT LIKE 'contenttype_%';
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        available_tables = all_tables

    # --- Выбираем таблицу для поиска ---
    table_to_search = request.GET.get('table', '') # Получаем имя таблицы из параметра GET

    # Проверяем, что выбранная таблица существует в списке
    if table_to_search and table_to_search in available_tables:
        # --- Выполняем поиск ---
        field1 = request.GET.get('field1', '')
        field2 = request.GET.get('field2', '')
        field3 = request.GET.get('field3', '')
        field4 = request.GET.get('field4', '')
        field5 = request.GET.get('field5', '')

        # Используем выбранную таблицу в запросе
        # ВАЖНО: ЗАМЕНИТЕ ИМЕНА СТОЛБЦОВ НИЖЕ НА РЕАЛЬНЫЕ ИЗ ВАШЕЙ ЗАГРУЖЕННОЙ ТАБЛИЦЫ
        # Пример: если в таблице table_to_search есть столбцы name, age, city, status, code
        # и вы хотите их использовать для поиска и вывода:
        # search_fields = ['name', 'age', 'city', 'status', 'code']
        # result_fields = ['name', 'age', 'city', 'status', 'code', 'field6', 'field7', 'field8']
        # Или, если структура фиксирована и вы знаете её:
        # Пусть search_fields = первые 5 столбцов, result_fields = следующие 8 (или все остальные, если меньше)
        # Это гипотетически. В реальности структура может отличаться.
        # Лучше всего передавать имена столбцов как параметры или хранить их вместе с именем таблицы (например, в DBFUpload).
        # Для простоты в этом примере предположим, что в *любой* загруженной таблице есть столбцы:
        # search_col1, search_col2, search_col3, search_col4, search_col5
        # и
        # res_col1, res_col2, res_col3, res_col4, res_col5, res_col6, res_col7, res_col8
        # Это НЕПРАКТИЧНО. Нужно хранить структуру или передавать её.

        # --- НАЧАЛО: ВРЕМЕННЫЕ ИМЕНА СТОЛБЦОВ (ПРИМЕР) ---
        # ЗАМЕНИТЕ ЭТИ ИМЕНА НА РЕАЛЬНЫЕ ИЗ ВАШИХ DBF-ФАЙЛОВ ---
        search_fields = ['P2', 'ST2', 'GNR']
        result_fields = ['ST2', 'P1', 'DKR']
        # --- КОНЕЦ: ВРЕМЕННЫЕ ИМЕНА СТОЛБЦОВ ---

        # Составляем часть SELECT
        select_cols = ', '.join([f'"{col}"' for col in result_fields])
        # Составляем часть WHERE
        where_parts = []
        params = []
        for i, search_col in enumerate(search_fields):
            param_val = request.GET.get(f'field{i+1}', '')
            params.extend([param_val, f'%{param_val}%'])
            where_parts.append(f"(%s = '' OR \"{search_col}\" ILIKE %s)")

        where_clause = ' AND '.join(where_parts)
        sql_query = f'SELECT {select_cols} FROM "{table_to_search}" WHERE {where_clause};'

        with connection.cursor() as cursor:
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
    else:
        # Если таблица не выбрана или не найдена, просто передаём список таблиц
        # и не выполняем поиск
        table_to_search = None # Сбрасываем, если таблица не валидна


    # --- Передаём данные в шаблон ---
    return render(request, 'core/search.html', {
        'results': results,
        'available_tables': available_tables,
        'selected_table': table_to_search # Передаём выбранную таблицу для отображения в шаблоне
    })

@login_required
@user_passes_test(is_superuser) # Только суперпользователи
def upload_dbf(request):
    if request.method == 'POST' and request.FILES.get('dbf_file'):
        uploaded_file = request.FILES['dbf_file']
        filename = uploaded_file.name

        # Проверка расширения
        if not filename.lower().endswith('.dbf'):
            # Обработка ошибки: неверный формат файла
            return render(request, 'core/upload_dbf.html', {'error': 'Файл должен быть в формате .dbf'})

        # Получаем имя таблицы из имени файла (без расширения)
        table_name = os.path.splitext(filename)[0]
        print(f"DEBUG: Original filename: {filename}, Derived table_name: {table_name}") # <-- Отладка

        # Проверка имени таблицы на безопасность (только буквы, цифры, подчеркивания)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
             return render(request, 'core/upload_dbf.html', {'error': 'Имя файла содержит недопустимые символы для имени таблицы.'})

        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Читаем DBF-файл с кодировкой cp866 (DOS)
            table = dbfread.DBF(temp_file_path, encoding='cp866')
            records = list(table)

            if not records:
                os.unlink(temp_file_path)
                return render(request, 'core/upload_dbf.html', {'error': 'Файл DBF пуст.'})

            # Получаем имена полей из DBF
            field_names = list(records[0].keys())

            # --- Определение максимальных длин строковых полей по ВСЕМ записям и определение типов ---
            max_lengths = {}
            type_hints = {} # Словарь для хранения признака, что поле содержит числа (пока грубо)

            for record in records:
                for field_name, value in record.items():
                    # Определяем тип значения в Python
                    val_type = type(value)
                    str_val = str(value) if value is not None else ""

                    # Обновляем максимальную длину для строк, независимо от "типа" в DBF
                    # Если значение - строка или None, проверяем его длину
                    if isinstance(value, str) or value is None:
                         current_len = len(str_val)
                         if field_name not in max_lengths or current_len > max_lengths[field_name]:
                             max_lengths[field_name] = current_len
                    # Если значение - число, запоминаем это (грубо)
                    elif isinstance(value, (int, float)):
                         # Пока просто отметим, что в этом поле был числовой тип
                         # Это не идеально, но помогает в грубой классификации
                         if field_name not in type_hints:
                             type_hints[field_name] = set()
                         type_hints[field_name].add(val_type.__name__)

            # --- Определение типов полей для SQL ---
            field_types = {}
            for field_name in field_names:
                 # Берём значение из первой записи для грубой типизации
                 first_val = records[0][field_name]
                 first_val_type = type(first_val)

                 # Проверяем, было ли в этом поле числовое значение (грубо)
                 was_numeric = type_hints.get(field_name, set()).intersection({'int', 'float'})

                 # Если первое значение - число (int/float) и в других записях тоже были числа
                 if isinstance(first_val, (int, float)) and was_numeric:
                     if isinstance(first_val, int):
                         field_types[field_name] = 'INTEGER'
                     else: # float
                         field_types[field_name] = 'NUMERIC'
                 else:
                     # Для всех остальных случаев (включая строки, None, и числа, которые не числа в других записях)
                     # Используем строковый тип с максимальной длиной
                     max_len_for_field = max_lengths.get(field_name, 0)
                     final_length = max(255, max_len_for_field) # Минимум 255
                     field_types[field_name] = f'VARCHAR({final_length})'

            # print(f"DEBUG: field_types = {field_types}") # Для отладки
            # print(f"DEBUG: max_lengths = {max_lengths}") # Для отладки
            # print(f"DEBUG: type_hints = {type_hints}") # Для отладки
            # Удаляем временный файл
            os.unlink(temp_file_path)

            # Создаем таблицу в PostgreSQL
            with connection.cursor() as cursor:
                # --- УДАЛЯЕМ ТАБЛИЦУ, ЕСЛИ ОНА СУЩЕСТВУЕТ ---
                drop_sql = f"DROP TABLE IF EXISTS \"{table_name}\";"
                cursor.execute(drop_sql)
                # ---

                # Составляем SQL для создания таблицы
                create_sql_parts = []
                for field_name, field_type in field_types.items():
                    # Экранируем имя поля, на случай если оно совпадает с ключевым словом
                    escaped_field_name = f'"{field_name}"'
                    create_sql_parts.append(f"{escaped_field_name} {field_type}")

                create_sql = f"CREATE TABLE \"{table_name}\" ({', '.join(create_sql_parts)});"
                cursor.execute(create_sql)

                # Составляем SQL для вставки данных
                if records:
                    # Подготавливаем столбцы
                    columns = ', '.join([f'"{name}"' for name in field_names])
                    # Подготавливаем плейсхолдеры для значений
                    placeholders = ', '.join(['%s'] * len(field_names))
                    insert_sql = f"INSERT INTO \"{table_name}\" ({columns}) VALUES ({placeholders});"

                    # Подготавливаем данные для вставки
                    data_to_insert = []
                    for record in records:
                        row_data = [record[field_name] for field_name in field_names]
                        data_to_insert.append(tuple(row_data))

                    # Выполняем вставку
                    cursor.executemany(insert_sql, data_to_insert)

            # Сохраняем запись о загрузке (если используем модель)
            # DBFUpload.objects.create(
            #     filename=filename,
            #     table_name=table_name,
            #     uploaded_by=request.user
            # )

            # Успешно
            return redirect('core:search') # Перенаправляем на страницу поиска или другую

        except Exception as e:
            # Удаляем временный файл в случае ошибки
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            # Обработка ошибки
            return render(request, 'core/upload_dbf.html', {'error': f'Ошибка обработки файла: {str(e)}'})

    return render(request, 'core/upload_dbf.html')
