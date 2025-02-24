from django.contrib import admin

from . import models


@admin.register(models.MailmanServer)
class MailmanServerAdmin(admin.ModelAdmin):
    list_display = (
        "url",
        "username",
        "enabled",
    )
    list_filter = ("enabled",)


@admin.register(models.Mailinglist)
class MailinlistAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "server",
        "enabled",
    )
    list_filter = ("enabled", "server")
