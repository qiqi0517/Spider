from django.urls import path
from . import views

urlpatterns = [
    path('', views.song_list, name="song_list"),
    path('song/<str:song_id>/', views.song_detail, name="song_detail"),
    path('singer/', views.singer_list, name="singer_list"),
    path('singer/<str:singer_id>/', views.singer_detail, name="singer_detail"),
    path('search/', views.search_result, name="search_result"),
    path("comment/<str:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("song/<str:song_id>/createcomment/", views.create_comment, name="create_comment"),
]
