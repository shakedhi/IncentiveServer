from django import forms
from .models import Incentive


class IncentiveFrom(forms.ModelForm):
    class Meta:
        model = Incentive


class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file'
    )


class getUserForm(forms.Form):
     userID = forms.CharField(label='userID')
     created_at = forms.CharField(label='created_at', max_length=1000)

