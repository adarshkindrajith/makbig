from django import forms
from .models import HelpRequest

class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ['request_type', 'message']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'border p-2 rounded'}),
            'message': forms.Textarea(attrs={'class': 'border p-2 rounded', 'rows': 4}),
        }
