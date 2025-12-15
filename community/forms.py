from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    """Form for creating/editing posts"""
    
    class Meta:
        model = Post
        fields = ['content', 'category', 'tags', 'location']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your thoughts with the community...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Add tags (e.g. #maize #rain #market)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your location (optional)'
            }),
        }


class CommentForm(forms.ModelForm):
    """Form for adding comments"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a comment...'
            }),
        }
