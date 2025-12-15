from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/save/', views.toggle_save_post, name='toggle_save_post'),
    path('post/<int:post_id>/report/', views.report_post, name='report_post'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('saved/', views.saved_posts, name='saved_posts'),
    path('user/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
]
