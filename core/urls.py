from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Event API
    path('api/events/', views.schedule_api, name='schedule_api'),
    path('api/events/add/', views.add_event, name='add_event'),
    path('api/events/<int:event_id>/update/', views.update_event, name='update_event'),
    path('api/events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # Journal API
    path('api/journal/', views.journal_list, name='journal_list'),
    path('api/journal/add/', views.add_journal_entry, name='add_journal_entry'),
    path('api/journal/<int:entry_id>/delete/', views.delete_journal_entry, name='delete_journal_entry'),
]
