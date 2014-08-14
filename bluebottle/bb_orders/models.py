from bluebottle.utils.utils import get_model_class
from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from uuidfield import UUIDField
from django.db.models import options
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer','preview_serializer', 'manage_serializer')

DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')


class OrderStatuses(DjangoChoices):
    cart = ChoiceItem('cart', label=_("Cart"))
    frozen = ChoiceItem('frozen', label=_("Frozen"))
    closed = ChoiceItem('closed', label=_("Closed"))


class BaseOrder(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=OrderStatuses.choices, default=OrderStatuses.cart, db_index=True)

    uuid = UUIDField(verbose_name=("Order number"), auto=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    country = models.ForeignKey('geo.Country', blank=True, null=True)
    total = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2, default=0)

    class Meta:
        abstract = True
        default_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        preview_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        manage_serializer = 'bluebottle.bb_orders.serializers.ManageOrderSerializer'

@receiver(post_save, weak=False, sender=DONATION_MODEL, dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    order = instance.order
    donations = DONATION_MODEL.objects.filter(order=order)
    total = donations.aggregate(Sum('amount'))['amount__sum']
    order.total = total
    order.save()