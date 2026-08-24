from django.urls import path
from . import views

urlpatterns = [
    path('', views.song_list, name="song_list"),
    path('song/<str:id>/', views.song_detail, name="song_detail"),
    path('singer/', views.singer_list, name="singer_list"),
    path('singer/<str:id>/', views.singer_detail, name="singer_detail"),
    path('search/', views.search_result, name="search_result"),
    path("comment/<str:id>/delete/", views.delete_comment, name="delete_comment"),
    path("song/<str:id>/createcomment/", views.create_comment, name="create_comment"),
]