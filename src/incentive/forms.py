from django import forms
from .models import Incentive, Timeout


class IncentiveForm(forms.ModelForm):
    class Meta:
        model = Incentive
        fields = ('owner', 'schemeName', 'schemeID', 'text', 'typeID', 'typeName',
                  'status', 'ordinal', 'tags', 'modeID', 'groupIncentive', 'condition')


class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file'
    )


class getUserForm(forms.Form):
    userID = forms.CharField(label='userID')
    created_at = forms.CharField(label='created_at', max_length=1000)


class TimeoutForm(forms.ModelForm):
    timeout = forms.IntegerField(min_value=1)

    class Meta:
        model = Timeout
        fields = ('timeout',)

