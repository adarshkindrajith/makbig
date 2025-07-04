from django import forms
from . models import dbstudent1
from learning.models import Course



class teacherloginform(forms.Form):  # This must match exactly
    t_email = forms.EmailField(label='email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    t_password = forms.CharField(label='password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))



class studentregistrationform(forms.ModelForm):
    QUALIFICATION_CHOICES = [
        ('Higher Secondary', 'Higher Secondary (12th Grade)'),
        ('Diploma', 'Diploma'),
        ('Bachelors', "Bachelor's Degree"),
        ('Masters', "Master's Degree"),
        ('PhD', 'PhD'),
        ('Other', 'Other'),
    ]

    s_qualification = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
        })
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=True,
        label="Select Course",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    s_profilepicture = forms.ImageField(required=True)
    
    class Meta:
        model = dbstudent1
        fields = [
            's_profilepicture', 's_firstname', 's_lastname', 's_email',
            's_phonenumber', 's_guardianphonenumber', 's_qualification', 'course'
        ]
        widgets = {
            's_profilepic': forms.ClearableFileInput(attrs={'class': 'hidden', 'id': 'id_s_profilepic'}),
            's_firstname': forms.TextInput(attrs={'class': 'form-control'}),
            's_lastname': forms.TextInput(attrs={'class': 'form-control'}),
            's_email': forms.EmailInput(attrs={'class': 'form-control'}),
            's_phonenumber': forms.TextInput(attrs={'class': 'form-control'}),
            's_guardianphonenumber': forms.TextInput(attrs={'class': 'form-control'}),
        }
