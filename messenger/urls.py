from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from chat.views import ChatViewSet, MessageViewSet, index, logout_view, signup, profile  # добавляем profile
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'chat', ChatViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), 
    path('', include('chat.urls')),  
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', signup, name='signup'),  # добавляем маршрут для регистрации
    path('profile/', profile, name='profile'),  # добавляем URL для профиля
    path('', index, name='index'), 
    path('logout/', logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)