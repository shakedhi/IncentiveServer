from django.db import models
from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles
# Create your models here.

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted((item, item) for item in get_all_styles())


class Tag(models.Model):
    # incentiveID = models.ForeignKey(Incentive,related_name="tags")
    tagID = models.IntegerField(null=False)
    tagName = models.CharField(max_length=100)

    # class Meta:
    # unique_together = ('incentiveID','tagID')

    def __unicode__(self):
        return '%d: %s' % (self.tagID, self.tagName)


class Incentive(models.Model):
    owner = models.ForeignKey('auth.User', related_name='incentive')
    # highlighted = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    schemeID = models.IntegerField(default=0)
    schemeName = models.CharField(max_length=100, blank=True, default='')
    typeID = models.IntegerField(default=0)
    typeName = models.CharField(max_length=100, blank=True, default='')
    status = models.BooleanField(default=True)
    ordinal = models.IntegerField(null=True, blank=True, default=0)
    modeID = models.IntegerField(default=0)
    presentationDuration = models.DateTimeField(auto_now_add=True)
    groupIncentive = models.BooleanField(default=False)
    text = models.TextField()
    tags = models.ManyToManyField(Tag, null=True, blank=True)
    # image = models.ImageField()
    condition = models.TextField()

    # tags = models.ManyToManyField(Tag, null=True, blank=True,related_name="tags")
    # code = models.TextField()
    # language = models.CharField(choices=LANGUAGE_CHOICES, default='python', max_length=100)
    # email = models.TextField()

    class Meta:
        ordering = ('created',)

    def user_can_manage_me(self, user):
        return user == self.owner

    def save(self, *args, **kwargs):
        """
        Use the `pygments` library to create a highlighted HTML
        representation of the code snippet.
        """
        super(Incentive, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%d: %s' % (self.schemeID, self.schemeName)


class Document(models.Model):
    owner = models.ForeignKey('auth.User', related_name='document')
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')


class Timeout(models.Model):
    timeout = models.IntegerField(null=False)

    @staticmethod
    def current_timeout():
        return Timeout.objects.all().first()

    def save(self, *args, **kwargs):
        """
        Use the `pygments` library to create a highlighted HTML
        representation of the code snippet.
        """
        Timeout.objects.all().delete()
        super(Timeout, self).save(*args, **kwargs)

    class Meta:
        ordering = ('timeout',)


class User(models.Model):
    user_id = models.CharField(max_length=1000, null=False)
    created_at = models.CharField(max_length=1000, null=False)

    class Meta:
        ordering = ('user_id', 'created_at')


class Collective(models.Model):
    collective_id = models.CharField(max_length=1000, null=False)
    incentive_text = models.CharField(max_length=1000, null=False)
    incentive_timestamp = models.BigIntegerField(null=False)

    class Meta:
        ordering = ('collective_id', 'incentive_text', 'incentive_timestamp')


class Invalidate(models.Model):
    peer_ids = models.CharField(max_length=1000, null=False)

    class Meta:
        ordering = ('peer_ids',)


class PeersAndCollectives(models.Model):
    project_name = models.CharField(max_length=1000, null=False)
    user_type = models.CharField(max_length=1000, null=False)
    user_id = models.CharField(max_length=1000, null=False)
    incentive_type = models.CharField(max_length=1000, null=False)
    incentive_text = models.CharField(max_length=1000, null=False)
    incentive_timestamp = models.BigIntegerField(null=True)

    class Meta:
        ordering = ('project_name', 'user_type', 'user_id', 'incentive_type', 'incentive_text', 'incentive_timestamp')
