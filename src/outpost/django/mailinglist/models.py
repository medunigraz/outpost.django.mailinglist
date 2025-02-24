from django.db import models
from django.utils.text import slugify
from outpost.django.base.decorators import signal_connect


class MailmanServer(models.Model):
    url = models.URLField()
    username = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    enabled = models.BooleanField(default=False)
    student_domain = models.CharField(max_length=256, null=True, blank=True)
    personal_domain = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return str(self.url)


@signal_connect
class Mailinglist(models.Model):
    server = models.ForeignKey(MailmanServer, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        "campusonline.Organization",
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        related_name="+",
    )
    name = models.CharField(max_length=1024, blank=True, null=True)
    domain = models.CharField(max_length=1024, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    moderators = models.ManyToManyField(
        "campusonline.Person",
        db_constraint=False,
        related_name="+",
    )

    def __str__(self):
        return str(self.organization)

    def pre_save(self, *args, **kwargs):
        if not self.name:
            self.name = slugify(self.organization)
