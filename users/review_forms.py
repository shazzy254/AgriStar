from django import forms
from users.review_models import FarmerReview

class FarmerReviewForm(forms.ModelForm):
    """Form for buyers to review farmers"""
    
    rating = forms.ChoiceField(
        choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-input'}),
        label="Rating"
    )
    
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your experience with this farmer...'
        }),
        required=False,
        label="Review (Optional)"
    )
    
    class Meta:
        model = FarmerReview
        fields = ['rating', 'review_text']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs.update({'class': 'star-rating'})
