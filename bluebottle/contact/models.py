from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from djchoices import DjangoChoices, ChoiceItem


class ContactMessage(models.Model):
    """
    Message sent from Contact Page
    """

    class ContactStatus(DjangoChoices):
        new = ChoiceItem('new', label=_("New"))
        in_progress = ChoiceItem('in progress', label=_("In progress"))
        closed = ChoiceItem('closed', label=_("Closed"))

    status = models.CharField(_('status'), max_length=20, choices=ContactStatus.choices, default=ContactStatus.new)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('author'), blank=True, null=True)
    name = models.CharField(_("Name"), max_length=200)
    email = models.EmailField(_("Email"), max_length=200)
    message = models.TextField(_("Message"))

    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    def __unicode__(self):
        return self.message[0:30]