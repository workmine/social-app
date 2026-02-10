from django.contrib import admin
from django.urls import path
from feed import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('like/<int:pk>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('search/', views.search_users, name='search_users'),
    path('delete/<int:pk>/', views.delete_post, name='delete_post'),
    
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<str:username>/', views.direct_message, name='direct_message'),
    
    path('accounts/login/', auth_views.LoginView.as_view(template_name='feed/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # ... existing urls ...
    path('api/like/<int:pk>/', views.like_post_api, name='like_post_api'),
    path('api/follow/<str:username>/', views.follow_user_api, name='follow_user_api'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)