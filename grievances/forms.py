
from django import forms
from .models import Grievance
from departments.models import Department, ComplaintCategory


class GrievanceForm(forms.ModelForm):

    class Meta:
        model = Grievance

        fields = [
            'department',
            'category',
            'title',
            'description',
            'address',
            'priority',
            'photograph',
        ]

        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_department',
            }),

            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category',
            }),

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter complaint title',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the civic issue...',
            }),

            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter the location/address of the issue',
            }),

            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),

            'photograph': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['department'].queryset = Department.objects.filter(
            is_active=True
        )

        department_id = self.data.get('department') or self.initial.get('department')

        if department_id:
            self.fields['category'].queryset = ComplaintCategory.objects.filter(
                department_id=department_id,
                is_active=True,
                department__is_active=True
            )
        else:
            self.fields['category'].queryset = ComplaintCategory.objects.none()

        self.fields['photograph'].required = False

    def clean(self):
        cleaned_data = super().clean()

        department = cleaned_data.get('department')
        category = cleaned_data.get('category')

        if department and category:
            if category.department_id != department.id:
                self.add_error(
                    'category',
                    'Please select a category belonging to the selected department.'
                )

        return cleaned_data
