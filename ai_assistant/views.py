from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import AIService
from .models import ChatSession, ChatMessage
from django.shortcuts import get_object_or_404

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        language = request.data.get('language', 'en')
        session_id = request.data.get('session_id')

        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or Create Session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            # Create title from first few words of message
            title = message[:30] + "..." if len(message) > 30 else message
            session = ChatSession.objects.create(user=request.user, title=title)
        
        # Save User Message
        ChatMessage.objects.create(session=session, sender='user', text=message)

        # Get AI Response
        response_text = AIService.chat_response(message, language)

        # Save AI Message
        ChatMessage.objects.create(session=session, sender='bot', text=response_text)
        
        return Response({
            'response': response_text,
            'session_id': session.id,
            'session_title': session.title
        })

class PublicChatView(APIView):
    # Allow any user (authenticated or not) to chat
    permission_classes = [] 
    authentication_classes = []

    def post(self, request):
        message = request.data.get('message')
        # Default to English but could infer from request
        language = request.data.get('language', 'en') 
        
        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        response = AIService.chat_response(message, language)
        return Response({'response': response})

class DiagnoseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'Image is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real app, you'd save the image or pass the file stream to the model
        result = AIService.diagnose_pest(image)
        return Response(result)

class AssistantView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.shortcuts import render
        sessions = ChatSession.objects.filter(user=request.user)
        return render(request, 'ai_assistant/index.html', {'sessions': sessions})

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        messages = session.messages.all().order_by('created_at')
        
        data = []
        for msg in messages:
            data.append({
                'sender': msg.sender,
                'text': msg.text,
                'audio_url': msg.audio_file.url if msg.audio_file else None,
                'image_url': msg.image_file.url if msg.image_file else None,
                'created_at': msg.created_at
            })
        return Response({'messages': data})
    
    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.delete()
        return Response({'success': True, 'message': 'Chat deleted successfully'})
    
    def put(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        new_title = request.data.get('title')
        if new_title:
            session.title = new_title
            session.save()
            return Response({'success': True, 'title': session.title})
        return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)

class VoiceChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        audio_file = request.FILES.get('audio')
        language = request.data.get('language', 'en')
        session_id = request.data.get('session_id')
        
        if not audio_file:
            return Response({'error': 'Audio file is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Transcribe
        transcript = AIService.transcribe_audio(audio_file)
        if not transcript:
            return Response({'error': 'Transcription failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # Get or Create Session (Title from transcript)
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            title = transcript[:30] + "..." if len(transcript) > 30 else transcript
            session = ChatSession.objects.create(user=request.user, title=title)

        # Save User Message (Audio + Text)
        ChatMessage.objects.create(session=session, sender='user', text=transcript, audio_file=audio_file)

        # 2. Get AI Response
        chat_response = AIService.chat_response(transcript, language)

        # Save AI Message
        ChatMessage.objects.create(session=session, sender='bot', text=chat_response)
        
        return Response({
            'transcript': transcript,
            'response': chat_response,
            'session_id': session.id,
            'session_title': session.title
        })

class VisionChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        image_file = request.FILES.get('image')
        prompt = request.data.get('message', 'Describe this image.')
        language = request.data.get('language', 'en')
        session_id = request.data.get('session_id')
        
        if not image_file:
            return Response({'error': 'Image file is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get or Create Session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(user=request.user, title="Image Analysis")

        # Save User Message (Image + Prompt)
        ChatMessage.objects.create(session=session, sender='user', text=prompt, image_file=image_file)

        # Analyze Image
        analysis = AIService.analyze_image(image_file, prompt, language)
        
        # Save AI Message
        ChatMessage.objects.create(session=session, sender='bot', text=analysis)
        
        return Response({
            'response': analysis,
            'session_id': session.id,
            'session_title': session.title
        })

class TranslateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text')
        target_lang = request.data.get('target_lang', 'sw')
        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .services import AIService
        translation = AIService.translate_text(text, target_lang)
        return Response({'translation': translation})
