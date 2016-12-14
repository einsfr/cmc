import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from cmcdispatcher.db import OrderedModel

# Create your models here.


class TaskGroup(OrderedModel):

    class Meta(OrderedModel.Meta):
        verbose_name = _('Группа заданий')
        verbose_name_plural = _('Группы заданий')
        default_permissions = ()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
