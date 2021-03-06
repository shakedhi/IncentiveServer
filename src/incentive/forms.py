from django import forms
from .models import Incentive, Timeout, User, Collective, PeersAndCollectives, ChangePassword


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
        model = Collective
        ordering = ('collective_id', 'incentive_text', 'incentive_timestamp')


class InvalidateForm(forms.ModelForm):
    peer_ids = forms.CharField(required=True)

    class Meta:
        model = Timeout
        fields = ('peer_ids',)


class PeersOrCollectivesForm(forms.Form):
    user_choices = [('peer', 'Peer'), ('collective', 'Collective')]
    inc_choices = [('message', 'Message'), ('preconfigured', 'Preconfigured')]
    ts_msg = "If you want to send the incentive after a timeout instead of using timestamp, " \
             "leave the field above empty."

    project_name = forms.CharField(required=True)
    user_type = forms.ChoiceField(choices=user_choices, required=True)
    user_id = forms.CharField(required=True)
    incentive_type = forms.ChoiceField(choices=inc_choices, required=True)
    incentive_text = forms.CharField(required=True, label='Incentive text (Message) or ID (Preconfigured)')
    incentive_timestamp = forms.IntegerField(required=False, help_text=ts_msg)

    class Meta:
        model = PeersAndCollectives
        ordering = ('project_name', 'user_type', 'user_id', 'incentive_type', 'incentive_text', 'incentive_timestamp')


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(required=True)
    new_password = forms.CharField(required=True)
    repeat_new_password = forms.CharField(required=True)

    class Meta:
        model = ChangePassword
        fields = ('new_password', 'repeat_new_password')
