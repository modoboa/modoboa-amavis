# coding: utf-8
"""
Amavis forms.
"""

from django import forms
from django.utils.translation import ugettext as _

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms
from modoboa.parameters import tools as param_tools

from .models import Policy, Users


class DomainPolicyForm(forms.ModelForm):

    spam_subject_tag2_act = forms.BooleanField()

    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks',
                  'spam_tag2_level', 'spam_subject_tag2',
                  'spam_kill_level', 'bypass_banned_checks')
        widgets = {
            'bypass_virus_checks': form_utils.InlineRadioSelect(),
            'bypass_spam_checks': form_utils.InlineRadioSelect(),
            'spam_tag2_level': forms.TextInput(
                attrs={'class': 'form-control'}),
            'spam_kill_level': forms.TextInput(
                attrs={'class': 'form-control'}),
            'spam_subject_tag2': forms.TextInput(
                attrs={'class': 'form-control'}),
            'bypass_banned_checks': form_utils.InlineRadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.domain = kwargs["instance"]
            try:
                policy = Users.objects.get(
                    email="@%s" % self.domain.name).policy
                kwargs["instance"] = policy
            except (Users.DoesNotExist, Policy.DoesNotExist):
                del kwargs["instance"]
        super(DomainPolicyForm, self).__init__(*args, **kwargs)
        for field in self.fields.keys():
            self.fields[field].required = False

    def save(self, user, commit=True):
        policy = super(DomainPolicyForm, self).save(commit=False)
        for field in ['bypass_spam_checks', 'bypass_virus_checks',
                      'bypass_banned_checks']:
            if getattr(policy, field) == '':
                setattr(policy, field, None)

        if self.cleaned_data['spam_subject_tag2_act']:
            policy.spam_subject_tag2 = None

        if commit:
            policy.save()
            try:
                u = Users.objects.get(fullname=policy.policy_name)
            except Users.DoesNotExist:
                u = Users.objects.get(email="@%s" % self.domain.name)
                u.policy = policy
                policy.save()
        return policy


class LearningRecipientForm(forms.Form):
    """A form to select the recipient of a learning request."""

    recipient = forms.ChoiceField(
        label=None, choices=[]
    )
    ltype = forms.ChoiceField(
        label="", choices=[("spam", "spam"), ("ham", "ham")],
        widget=forms.widgets.HiddenInput
    )
    selection = forms.CharField(
        label="", widget=forms.widgets.HiddenInput)

    def __init__(self, user, *args, **kwargs):
        """Constructor."""
        super(LearningRecipientForm, self).__init__(*args, **kwargs)
        choices = []
        if user.role == "SuperAdmins":
            choices.append(("global", _("Global database")))
        conf = dict(param_tools.get_global_parameters("modoboa_amavis"))
        if conf["domain_level_learning"]:
            choices.append(("domain", _("Domain's database")))
        if conf["user_level_learning"]:
            choices.append(("user", _("User's database")))
        self.fields["recipient"].choices = choices


class ParametersForm(param_forms.AdminParametersForm):
    """Extension settings."""

    app = "modoboa_amavis"

    qsettings_sep = form_utils.SeparatorField(label=_("Quarantine settings"))

    max_messages_age = forms.IntegerField(
        label=_("Maximum message age"),
        initial=14,
        help_text=_(
            "Quarantine messages maximum age (in days) before deletion"
        )
    )

    sep1 = form_utils.SeparatorField(label=_("Messages releasing"))

    released_msgs_cleanup = form_utils.YesNoField(
        label=_("Remove released messages"),
        initial=False,
        help_text=_("Remove messages marked as released while cleaning up "
                    "the database")
    )

    am_pdp_mode = forms.ChoiceField(
        label=_("Amavis connection mode"),
        choices=[("inet", "inet"), ("unix", "unix")],
        initial="unix",
        help_text=_("Mode used to access the PDP server"),
        widget=form_utils.InlineRadioSelect(attrs={"type": "checkbox"})
    )

    am_pdp_host = forms.CharField(
        label=_("PDP server address"),
        initial="localhost",
        help_text=_("PDP server address (if inet mode)"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    am_pdp_port = forms.IntegerField(
        label=_("PDP server port"),
        initial=9998,
        help_text=_("PDP server port (if inet mode)")
    )

    am_pdp_socket = forms.CharField(
        label=_("PDP server socket"),
        initial="/var/amavis/amavisd.sock",
        help_text=_("Path to the PDP server socket (if unix mode)")
    )

    user_can_release = form_utils.YesNoField(
        label=_("Allow direct release"),
        initial=False,
        help_text=_("Allow users to directly release their messages")
    )

    self_service = form_utils.YesNoField(
        label=_("Enable self-service mode"),
        initial=False,
        help_text=_("Activate the 'self-service' mode")
    )

    notifications_sender = forms.EmailField(
        label=_("Notifications sender"),
        initial="notification@modoboa.org",
        help_text=_("The e-mail address used to send notitications")
    )

    lsep = form_utils.SeparatorField(label=_("Manual learning"))

    manual_learning = form_utils.YesNoField(
        label=_("Enable manual learning"),
        initial=True,
        help_text=_(
            "Allow super administrators to manually train Spamassassin"
        )
    )

    sa_is_local = form_utils.YesNoField(
        label=_("Is Spamassassin local?"),
        initial=True,
        help_text=_(
            "Tell if Spamassassin is running on the same server than modoboa"
        )
    )

    default_user = forms.CharField(
        label=_("Default user"),
        initial="amavis",
        help_text=_(
            "Name of the user owning the default bayesian database"
        )
    )

    spamd_address = forms.CharField(
        label=_("Spamd address"),
        initial="127.0.0.1",
        help_text=_("The IP address where spamd can be reached")
    )

    spamd_port = forms.IntegerField(
        label=_("Spamd port"),
        initial=783,
        help_text=_("The TCP port spamd is listening on")
    )

    domain_level_learning = form_utils.YesNoField(
        label=_("Enable per-domain manual learning"),
        initial=False,
        help_text=_(
            "Allow domain administrators to train Spamassassin "
            "(within dedicated per-domain databases)"
        )
    )

    user_level_learning = form_utils.YesNoField(
        label=_("Enable per-user manual learning"),
        initial=False,
        help_text=_(
            "Allow simple users to personally train Spamassassin "
            "(within a dedicated database)"
        )
    )

    visibility_rules = {
        "am_pdp_host": "am_pdp_mode=inet",
        "am_pdp_port": "am_pdp_mode=inet",
        "am_pdp_socket": "am_pdp_mode=unix",

        "sa_is_local": "manual_learning=yes",
        "default_user": "manual_learning=yes",
        "spamd_address": "sa_is_local=no",
        "spamd_port": "sa_is_local=no",
        "domain_level_learning": "manual_learning=yes",
        "user_level_learning": "manual_learning=yes"
    }


class UserSettings(param_forms.UserParametersForm):
    """Per-user settings."""

    app = "modoboa_amavis"

    dsep = form_utils.SeparatorField(label=_("Display"))

    messages_per_page = forms.IntegerField(
        initial=40,
        label=_("Number of displayed emails per page"),
        help_text=_("Set the maximum number of messages displayed in a page")
    )
