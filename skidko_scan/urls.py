from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Админ-панель
    path('admin/', admin.site.urls),

    # Фиды (админка загрузки)
    path('admin/feeds/', include('apps.feeds.urls', namespace='feeds')),

    # Основное приложение (главная, товары, категории, подкатегории)
    path("", include("apps.products.urls")),

    # Приложение core (профили пользователей и т.п.)
    path("", include("apps.core.urls")),
]


# Static & Media при DEBUG=True
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
