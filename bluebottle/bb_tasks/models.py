from bluebottle.utils.utils import get_taskmember_model
from django.conf import settings
from django.db import models
import django.db.models.options as options

from django.utils.translation import ugettext as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from taggit.managers import TaggableManager

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',)

class BaseSkill(models.Model):

    name = models.CharField(_('english name'), max_length=100, unique=True)
    name_nl = models.CharField(_('dutch name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id', )
        abstract = True


class BaseTaskMember(models.Model):
    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_('Applied'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        stopped = ChoiceItem('stopped', label=_('Stopped'))
        realized = ChoiceItem('realized', label=_('Realised'))

    member = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    task = models.ForeignKey(settings.TASKS_TASK_MODEL, related_name="members")
    status = models.CharField(_('status'), max_length=20, choices=TaskMemberStatuses.choices,
                              default=TaskMemberStatuses.applied)
    motivation = models.TextField(
        _('Motivation'), help_text=_('Motivation by applicant.'), blank=True)
    comment = models.TextField(_('Comment'), help_text=_('Comment by task owner.'), blank=True)
    time_spent = models.PositiveSmallIntegerField(
        _('time spent'), default=0, help_text=_('Time spent executing this task.'))

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    _initial_status = None

    #objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super(BaseTaskMember, self).__init__(*args, **kwargs)
        self._initial_status = self.status

    def save(self, *args, **kwargs):
        if self._initial_status != self.status:
            self._number_of_members_needed(self.task)

        super(BaseTaskMember, self).save(*args, **kwargs)
        self._initial_status = self.status

    def _number_of_members_needed(self, task):
        BB_TASKMEMBER_MODEL = get_taskmember_model()
        members_accepted = BB_TASKMEMBER_MODEL.objects.filter(task=task).all().count()
        if task.status == 'open' and task.people_needed <= members_accepted:
            task.set_in_progress()


    class Meta:
        abstract = True


class BaseTaskFile(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    title = models.CharField(max_length=255)
    file = models.FileField(_('file'), upload_to='task_files/')
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('Updated'))
    task = models.ForeignKey(settings.TASKS_TASK_MODEL, related_name="files")

    class Meta:
        abstract = True


class BaseTask(models.Model):
    """ The base Task model """

    # We should probably turn this into another class model like the projectphase
    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        in_progress = ChoiceItem('in progress', label=_('In progress'))
        closed = ChoiceItem('closed', label=_('Closed'))
        realized = ChoiceItem('realized', label=_('Realised'))

    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    end_goal = models.TextField(_('end_goal'))
    location = models.CharField(_('location'), max_length=200)
    people_needed = models.PositiveIntegerField(_('people needed'), default=1)

    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    # See Django docs on issues with related name and an (abstract) base class:
    # https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    status = models.CharField(
        _('status'), max_length=20, choices=TaskStatuses.choices,
        default=TaskStatuses.open)
    date_status_change = models.DateTimeField(_('date status change'), blank=True, null=True)

    deadline = models.DateTimeField()
    tags = TaggableManager(blank=True, verbose_name=_('tags'))

    objects = models.Manager()

    # required resources
    time_needed = models.CharField(
        _('time_needed'), max_length=200,
        help_text=_('Estimated number of hours needed to perform this task.'))
    skill = models.ForeignKey(settings.TASKS_SKILL_MODEL, verbose_name=_('Skill needed'), null=True)

    # internal usage
    created = CreationDateTimeField(
        _('created'), help_text=_('When this task was created?'))
    updated = ModificationDateTimeField(_('updated'))

    class Meta:
        default_serializer = 'bluebottle.bb_tasks.serializers.BaseTaskSerializer'
        abstract = True
        ordering = ['-created']
        verbose_name = _(u'task')
        verbose_name_plural = _(u'tasks')

    def __init__(self, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)
        self._original_status = self.status

    def __unicode__(self):
        return self.title

    def set_in_progress(self):
        self.status = self.TaskStatuses.in_progress
        self.save()


