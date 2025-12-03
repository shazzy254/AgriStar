from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import FarmerSchedule, JournalEntry
from marketplace.models import Notification
import json
from datetime import timedelta

@login_required
def calendar_view(request):
    """Render the main calendar and journal page"""
    # Check for upcoming events and create notifications
    check_upcoming_events(request.user)
    return render(request, 'core/calendar.html')

@login_required
def schedule_api(request):
    """API to get all events for the calendar"""
    events = FarmerSchedule.objects.filter(farmer=request.user)
    event_list = []
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'description': event.description,
            'extendedProps': {
                'eventType': event.event_type,
                'status': event.status,
                'isReminder': event.is_reminder,
                'reminderMinutes': event.reminder_minutes
            },
            'backgroundColor': get_event_color(event.event_type),
            'borderColor': get_event_color(event.event_type)
        })
    return JsonResponse(event_list, safe=False)

@login_required
@require_POST
def add_event(request):
    """Add a new calendar event"""
    try:
        data = json.loads(request.body)
        event = FarmerSchedule.objects.create(
            farmer=request.user,
            title=data.get('title'),
            start_time=data.get('start'),
            end_time=data.get('end'),
            description=data.get('description', ''),
            event_type=data.get('event_type', 'OTHER'),
            is_reminder=data.get('is_reminder', True),
            reminder_minutes=int(data.get('reminder_minutes', 30))
        )
        return JsonResponse({'success': True, 'id': event.id, 'message': 'Event added successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def update_event(request, event_id):
    """Update an existing event"""
    try:
        event = get_object_or_404(FarmerSchedule, id=event_id, farmer=request.user)
        data = json.loads(request.body)
        
        event.title = data.get('title', event.title)
        event.start_time = data.get('start', event.start_time)
        event.end_time = data.get('end', event.end_time)
        event.description = data.get('description', event.description)
        event.event_type = data.get('event_type', event.event_type)
        event.is_reminder = data.get('is_reminder', event.is_reminder)
        event.reminder_minutes = int(data.get('reminder_minutes', event.reminder_minutes))
        event.status = data.get('status', event.status)
        event.save()
        
        return JsonResponse({'success': True, 'message': 'Event updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def delete_event(request, event_id):
    """Delete an event"""
    try:
        event = get_object_or_404(FarmerSchedule, id=event_id, farmer=request.user)
        event.delete()
        return JsonResponse({'success': True, 'message': 'Event deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== JOURNAL VIEWS ====================

@login_required
def journal_list(request):
    """Get all journal entries"""
    entries = JournalEntry.objects.filter(farmer=request.user).order_by('-date', '-created_at')
    data = []
    for entry in entries:
        data.append({
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'date': entry.date.isoformat(),
            'created_at': entry.created_at.isoformat()
        })
    return JsonResponse(data, safe=False)

@login_required
@require_POST
def add_journal_entry(request):
    """Add a new journal entry"""
    try:
        data = json.loads(request.body)
        entry = JournalEntry.objects.create(
            farmer=request.user,
            title=data.get('title'),
            content=data.get('content'),
            date=data.get('date', timezone.now().date())
        )
        return JsonResponse({'success': True, 'id': entry.id, 'message': 'Journal entry saved'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def delete_journal_entry(request, entry_id):
    """Delete a journal entry"""
    try:
        entry = get_object_or_404(JournalEntry, id=entry_id, farmer=request.user)
        entry.delete()
        return JsonResponse({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== HELPER FUNCTIONS ====================

def get_event_color(event_type):
    colors = {
        'PLANTING': '#2ecc71',   # Green
        'HARVESTING': '#f1c40f', # Yellow
        'FERTILIZING': '#e67e22',# Orange
        'IRRIGATION': '#3498db', # Blue
        'MEETING': '#9b59b6',    # Purple
        'OTHER': '#95a5a6'       # Gray
    }
    return colors.get(event_type, '#95a5a6')

def check_upcoming_events(user):
    """Check for upcoming events and create notifications"""
    now = timezone.now()
    # Look for events in the next 24 hours that haven't passed yet
    upcoming_events = FarmerSchedule.objects.filter(
        farmer=user,
        start_time__gt=now,
        start_time__lte=now + timedelta(hours=24),
        is_reminder=True
    )
    
    for event in upcoming_events:
        # Check if notification time has arrived
        notification_time = event.start_time - timedelta(minutes=event.reminder_minutes)
        
        if now >= notification_time:
            # Check if notification already exists to avoid duplicates
            # We use a unique message or check recent notifications
            message = f"Reminder: {event.title} is coming up at {event.start_time.strftime('%H:%M')}"
            
            exists = Notification.objects.filter(
                user=user,
                message=message,
                created_at__gte=now - timedelta(hours=24)
            ).exists()
            
            if not exists:
                Notification.objects.create(
                    user=user,
                    notification_type='ORDER_ACCEPTED', # Reusing type or add 'REMINDER' if possible
                    message=message
                )

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')

def terms_view(request):
    return render(request, 'core/terms.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')
