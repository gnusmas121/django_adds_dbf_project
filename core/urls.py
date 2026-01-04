# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.search, name='search'), # Оставляем существующий
    path('upload_dbf/', views.upload_dbf, name='upload_dbf'), # Новый путь
    path('upload_dbf/', views.upload_dbf, name='upload_dbf'), # <-- Это должно быть
    path('upload_excel/', views.upload_excel, name='upload_excel'), # <-- Это должно быть
    path('get_table_columns/', views.get_table_columns, name='get_table_columns'), # <-- Это должно быть
    path('download_search_template/', views.download_search_template, name='download_search_template'), # <-- Это должно быть
    path('manage_table_template/', views.manage_table_template, name='manage_table_template'), # <-- Новый маршрут
    path('manage_table_template/<str:table_name>/', views.manage_table_template, name='manage_table_template_with_table'), # <-- Для редиректа
    # Убедитесь, что другие маршруты также правильно названы
    # path('upload_excel/', views.upload_excel, name='upload_excel'), # <-- Новый маршрут
    # path('get_table_columns/', views.get_table_columns, name='get_table_columns'), # <-- Новый маршрут
    # path('download_search_template/', views.download_search_template, name='download_search_template'), # <-- Новый маршрут
]