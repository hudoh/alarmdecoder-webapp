# -*- coding: utf-8 -*-

import json
from flask.ext.wtf import Form
from flask.ext.wtf.html5 import URLField, EmailField, TelField
import wtforms
from wtforms import (ValidationError, HiddenField, TextField, HiddenField,
        PasswordField, SubmitField, TextAreaField, IntegerField, RadioField,
        FileField, DecimalField, BooleanField, SelectField, FormField, FieldList,
        SelectMultipleField)
from wtforms.validators import (Required, Length, EqualTo, Email, NumberRange,
        URL, AnyOf, Optional)
from wtforms.widgets import ListWidget, CheckboxInput
from .constants import (NOTIFICATIONS, NOTIFICATION_TYPES, SUBSCRIPTIONS, DEFAULT_SUBSCRIPTIONS, EMAIL, GOOGLETALK, PUSHOVER, PUSHOVER_PRIORITIES, 
                        NMA_PRIORITIES, LOWEST, LOW, NORMAL, HIGH, EMERGENCY, PROWL_PRIORITIES)
from .models import NotificationSetting
from ..widgets import ButtonField, MultiCheckboxField


class NotificationButtonForm(wtforms.Form):
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications'")
    submit = SubmitField(u'Save')
    test = SubmitField(u'Save & Test')


class CreateNotificationForm(Form):
    type = SelectField(u'Notification Type', choices=[nt for t, nt in NOTIFICATIONS.iteritems()])

    submit = SubmitField(u'Next')
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications'")


class EditNotificationMessageForm(Form):
    id = HiddenField()
    text = TextAreaField(u'Message Text', [Required(), Length(max=255)])

    submit = SubmitField(u'Save')
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications/messages'")


class EditNotificationForm(Form):
    type = HiddenField()
    description = TextField(u'Description', [Required(), Length(max=255)], description=u'Brief description of this notification')
    subscriptions = MultiCheckboxField(u'Notify on..', choices=[(str(k), v) for k, v in SUBSCRIPTIONS.iteritems()])

    def populate_settings(self, settings, id=None):
        settings['subscriptions'] = self.populate_setting('subscriptions', json.dumps({str(k): True for k in self.subscriptions.data}))

    def populate_from_settings(self, id):
        subscriptions = self.populate_from_setting(id, 'subscriptions')
        if subscriptions:
            self.subscriptions.data = [k if v == True else False for k, v in json.loads(subscriptions).iteritems()]

    def populate_setting(self, name, value, id=None):
        if id is not None:
            setting = NotificationSetting.query.filter_by(notification_id=id, name=name).first()
        else:
            setting = NotificationSetting(name=name)

        setting.value = value

        return setting

    def populate_from_setting(self, id, name, default=None):
        ret = default

        setting = NotificationSetting.query.filter_by(notification_id=id, name=name).first()
        if setting is not None:
            ret = setting.value

        return ret


class EmailNotificationForm(EditNotificationForm):
    source = TextField(u'Source Address', [Required(), Length(max=255)], default='root@localhost', description=u'Emails will originate from this address')
    destination = TextField(u'Destination Address', [Required(), Length(max=255)], description=u'Emails will be sent to this address')

    subject = TextField(u'Email Subject', [Required(), Length(max=255)], default='AlarmDecoder: Alarm Event', description=u'Emails will contain this text as the subject')

    server = TextField(u'Email Server', [Required(), Length(max=255)], default='localhost')
    port = IntegerField(u'Server Port', [Required(), NumberRange(1, 65535)], default=25)
    tls = BooleanField(u'Use TLS?', default=False)
    authentication_required = BooleanField(u'Authenticate with email server?', default=False)
    username = TextField(u'Username', [Optional(), Length(max=255)])
    password = PasswordField(u'Password', [Optional(), Length(max=255)])

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)

        settings['source'] = self.populate_setting('source', self.source.data)
        settings['destination'] = self.populate_setting('destination', self.destination.data)
        settings['subject'] = self.populate_setting('subject', self.subject.data)
        settings['server'] = self.populate_setting('server', self.server.data)
        settings['port'] = self.populate_setting('port', self.port.data)
        settings['tls'] = self.populate_setting('tls', self.tls.data)
        settings['authentication_required'] = self.populate_setting('authentication_required', self.authentication_required.data)
        settings['username'] = self.populate_setting('username', self.username.data)
        settings['password'] = self.populate_setting('password', self.password.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)

        self.source.data = self.populate_from_setting(id, 'source')
        self.destination.data = self.populate_from_setting(id, 'destination')
        self.subject.data = self.populate_from_setting(id, 'subject')
        self.server.data = self.populate_from_setting(id, 'server')
        self.tls.data = self.populate_from_setting(id, 'tls')
        self.port.data = self.populate_from_setting(id, 'port')
        self.authentication_required.data = self.populate_from_setting(id, 'authentication_required')
        self.username.data = self.populate_from_setting(id, 'username')
        self.password.widget.hide_value = False
        self.password.data = self.populate_from_setting(id, 'password')


class GoogleTalkNotificationForm(EditNotificationForm):
    source = TextField(u'Source Address', [Required(), Length(max=255)], default='root@localhost', description=u'Messages will originate from this address')
    password = PasswordField(u'Password', [Required(), Length(max=255)], description=u'Password for the source account')
    destination = TextField(u'Destination Address', [Required(), Length(max=255)], description=u'Messages will be sent to this address')

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)
        settings['source'] = self.populate_setting('source', self.source.data)
        settings['password'] = self.populate_setting('password', self.password.data)
        settings['destination'] = self.populate_setting('destination', self.destination.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)
        self.source.data = self.populate_from_setting(id, 'source')
        self.password.widget.hide_value = False
        self.password.data = self.populate_from_setting(id, 'password')
        self.destination.data = self.populate_from_setting(id, 'destination')

class PushoverNotificationForm(EditNotificationForm):
    token = TextField(u'API Token', [Required(), Length(max=30)], description=u'Your Application\'s API Token')
    user_key = TextField(u'User/Group Key', [Required(), Length(max=30)], description=u'Your user or group key')
    priority = SelectField(u'Message Priority', choices=[PUSHOVER_PRIORITIES[LOWEST], PUSHOVER_PRIORITIES[LOW], PUSHOVER_PRIORITIES[NORMAL], PUSHOVER_PRIORITIES[HIGH], PUSHOVER_PRIORITIES[EMERGENCY]], default=PUSHOVER_PRIORITIES[LOW], description='Pushover message priority', coerce=int)
    title = TextField(u'Title of Message', [Length(max=255)], description=u'Title of Notification Messages')

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)
        settings['token'] = self.populate_setting('token', self.token.data)
        settings['user_key'] = self.populate_setting('user_key', self.user_key.data)
        settings['priority'] = self.populate_setting('priority', self.priority.data)
        settings['title'] = self.populate_setting('title', self.title.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)
        self.token.data = self.populate_from_setting(id, 'token')
        self.user_key.data = self.populate_from_setting(id, 'user_key')
        self.priority.data = self.populate_from_setting(id, 'priority')
        self.title.data = self.populate_from_setting(id, 'title')

class TwilioNotificationForm(EditNotificationForm):
    account_sid = TextField(u'Account SID', [Required(), Length(max=50)], description=u'Your Twilio Account SID')
    auth_token = TextField(u'Auth Token', [Required(), Length(max=50)], description=u'Your Twilio User Auth Token')
    number_to = TextField(u'To', [Required(), Length(max=15)], description=u'Number to send SMS to')
    number_from = TextField(u'From', [Required(), Length(max=15)], description=u'Must Be A Valid Twilio Phone Number')

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)
        settings['account_sid'] = self.populate_setting('account_sid', self.account_sid.data)
        settings['auth_token'] = self.populate_setting('auth_token', self.auth_token.data)
        settings['number_to'] = self.populate_setting('number_to', self.number_to.data)
        settings['number_from'] = self.populate_setting('number_from', self.number_from.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)
        self.account_sid.data = self.populate_from_setting(id, 'account_sid')
        self.auth_token.data = self.populate_from_setting(id, 'auth_token')
        self.number_to.data = self.populate_from_setting(id, 'number_to')
        self.number_from.data = self.populate_from_setting(id, 'number_from')

class NMANotificationForm(EditNotificationForm):
    api_key = TextField(u'API Key', [Required(), Length(max=50)], description=u'Your NotifyMyAndroid API Key')
    app_name = TextField(u'Application Name', [Required(), Length(max=256)], description=u'Application Name to Show in Notifications', default='AlarmDecoder')
    nma_priority = SelectField(u'Message Priority', choices=[NMA_PRIORITIES[LOWEST], NMA_PRIORITIES[LOW], NMA_PRIORITIES[NORMAL], NMA_PRIORITIES[HIGH], NMA_PRIORITIES[EMERGENCY]], default=NMA_PRIORITIES[LOW], description='NotifyMyAndroid message priority', coerce=int)
    
    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)
        settings['api_key'] = self.populate_setting('api_key', self.api_key.data)
        settings['app_name'] = self.populate_setting('app_name', self.app_name.data)
        settings['nma_priority'] = self.populate_setting('nma_priority', self.nma_priority.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)
        self.api_key.data = self.populate_from_setting(id, 'api_key')
        self.app_name.data = self.populate_from_setting(id, 'app_name')
        self.nma_priority.data = self.populate_from_setting(id, 'nma_priority')

class ProwlNotificationForm(EditNotificationForm):
    prowl_api_key = TextField(u'API Key', [Required(), Length(max=50)], description=u'Your Prowl API Key')
    prowl_app_name = TextField(u'Application Name', [Required(), Length(max=256)], description=u'Application Name to Show in Notifications', default='AlarmDecoder')
    prowl_priority = SelectField(u'Message Priority', choices=[PROWL_PRIORITIES[LOWEST], PROWL_PRIORITIES[LOW], PROWL_PRIORITIES[NORMAL], PROWL_PRIORITIES[HIGH], PROWL_PRIORITIES[EMERGENCY]], default=PROWL_PRIORITIES[LOW], description='Prowl message priority', coerce=int)

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)

        settings['prowl_api_key'] = self.populate_setting('prowl_api_key', self.prowl_api_key.data)
        settings['prowl_app_name'] = self.populate_setting('prowl_app_name', self.prowl_app_name.data)
        settings['prowl_priority'] = self.populate_setting('prowl_priority', self.prowl_priority.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)
        
        self.prowl_api_key.data = self.populate_from_setting(id, 'prowl_api_key')
        self.prowl_app_name.data = self.populate_from_setting(id, 'prowl_app_name')
        self.prowl_priority.data = self.populate_from_setting(id, 'prowl_priority')
