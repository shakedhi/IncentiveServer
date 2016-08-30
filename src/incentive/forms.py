from django import forms
from .models import Incentive, Timeout, User


class IncentiveForm(forms.ModelForm):
    class Meta:
        model = Incentive
        fields = ('owner', 'schemeName', 'schemeID', 'text', 'typeID', 'typeName',
                  'status', 'ordinal', 'tags', 'modeID', 'groupIncentive', 'condition')


class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file'
    )


class UserForm(forms.Form):
    user_id = forms.CharField(required=True)
    created_at = forms.CharField(required=True)

    class Meta:
        model = User
        ordering = ('user_id', 'created_at')


class TimeoutForm(forms.ModelForm):
    timeout = forms.IntegerField(min_value=1)

    class Meta:
        model = Timeout
        fields = ('timeout',)


class CollectiveForm(forms.Form):
    collective_id = forms.CharField(required=True)
    incentive_text = forms.CharField(required=True)
    incentive_timestamp = forms.IntegerField(required=True)

    class Meta:
        ordering = ('collective_id', 'incentive_text', 'incentive_timestamp')


class InvalidateForm(forms.ModelForm):
    peer_ids = forms.CharField(required=True)

    class Meta:
        model = Timeout
        fields = ('peer_ids',)
