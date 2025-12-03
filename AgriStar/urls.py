from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('marketplace/', include('marketplace.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('core/', include('core.urls')),
    path('custom-admin/', include('administration.urls')),
    path('mpesa/', include('mpesa.urls')),
    path('community/', include('community.urls')),
]

# Import after urlpatterns to avoid circular import
from core.views import landing_page, terms_view, privacy_view
urlpatterns.insert(0, path('', landing_page, name='home'))
urlpatterns.insert(1, path('terms/', terms_view, name='terms'))
urlpatterns.insert(2, path('privacy/', privacy_view, name='privacy'))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
