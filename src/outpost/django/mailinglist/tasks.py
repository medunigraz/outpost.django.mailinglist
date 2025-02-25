import logging

from celery import shared_task
from mailmanclient import Client
from outpost.django.campusonline import models as campusonline

from .conf import settings

logger = logging.getLogger(__name__)


class MailinglistTasks:
    @shared_task(
        bind=True, ignore_result=False, name=f"{__name__}.Mailinglist:organizations"
    )
    def organizations(task, dry_run=False):
        from . import models

        for ml in models.Mailinglist.objects.filter(enabled=True):
            logger.info(f"Updating mailinglist {ml}")
            client = Client(ml.server.url, ml.server.username, ml.server.password)
            domain = next((d for d in client.domains if d.mail_host == ml.domain), None)
            if not domain:
                logger.error(f"Domain {ml.domain} not available on {ml.server}.")
                continue
            mlist = next((li for li in domain.lists if li.list_name == ml.name), None)
            if not mlist:
                logger.info(
                    f"Creating new mailinglist {settings.MAILINGLIST_LIST_STYLE} on {domain.mail_host}"
                )
                mlist = domain.create_list(
                    ml.name, style_name=settings.MAILINGLIST_LIST_STYLE
                )
            for k, v in settings.MAILINGLIST_LIST_SETTINGS.items():
                logger.debug(f"Setting {k} to {v} on {mlist}")
                mlist.settings[k] = v
            mlist.settings["display_name"] = str(ml.organization)
            mlist.settings[
                "description"
            ] = f"Automatically managed list for {ml.organization}"
            mlist.settings.save()
            existing = set((m.email for m in mlist.members))
            names = {
                p.email.lower(): f"{p.last_name}, {p.first_name}"
                for p in ml.organization.persons.filter(employed=True)
            }
            proposed = set(names.keys())
            add = proposed - existing
            remove = existing - proposed
            for email in add:
                logger.debug(f"Subscribing {email} to {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.subscribe(
                        email,
                        display_name=names.get(email),
                        pre_verified=True,
                        pre_confirmed=True,
                        pre_approved=True,
                        invitation=False,
                    )
            for email in remove:
                logger.debug(f"Unsubscribing {email} from {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.unsubscribe(email)
            existing = set((m.email for m in mlist.moderators if m.email))
            proposed = set(
                (m.email for m in ml.moderators.filter(employed=True) if m.email)
            )
            add = proposed - existing
            remove = existing - proposed
            for email in add:
                logger.debug(f"Adding moderator {email} to {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.add_moderator(email)
            for email in remove:
                logger.debug(f"Removing moderator {email} from {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.remove_moderator(email)

    @shared_task(
        bind=True, ignore_result=False, name=f"{__name__}.Mailinglist:students"
    )
    def students(task, dry_run=False):
        from . import models

        for server in models.MailmanServer.objects.filter(student_domain__isnull=False):
            logger.info(f"Updating student mailinglist on {server}")
            client = Client(server.url, server.username, server.password)
            domain = next(
                (d for d in client.domains if d.mail_host == server.student_domain),
                None,
            )
            if not domain:
                logger.error(
                    f"Domain {server.student_domain} not available on {server}."
                )
                continue
            mlist = next(
                (
                    li
                    for li in domain.lists
                    if li.list_name == settings.MAILINGLIST_STUDENT_LIST
                ),
                None,
            )
            if not mlist:
                logger.info(
                    f"Creating new mailinglist {settings.MAILINGLIST_STUDENT_LIST} on {server.student_domain}"
                )
                mlist = domain.create_list(
                    settings.MAILINGLIST_STUDENT_LIST,
                    style_name=settings.MAILINGLIST_LIST_STYLE,
                )
            for k, v in settings.MAILINGLIST_LIST_SETTINGS.items():
                logger.debug(f"Setting {k} to {v} on {mlist}")
                mlist.settings[k] = v
            mlist.settings["display_name"] = "Students"
            mlist.settings["description"] = "Automatically managed list for students"
            mlist.settings.save()
            existing = set((m.email for m in mlist.members if m.email))
            proposed = set(
                (s.email.lower() for s in campusonline.Student.objects.all() if s.email)
            )
            add = proposed - existing
            remove = existing - proposed
            for email in add:
                logger.debug(f"Subscribing {email} to {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.subscribe(
                        email,
                        pre_verified=True,
                        pre_confirmed=True,
                        pre_approved=True,
                        invitation=False,
                    )
            for email in remove:
                logger.debug(f"Unsubscribing {email} from {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.unsubscribe(email)

    @shared_task(
        bind=True, ignore_result=False, name=f"{__name__}.Mailinglist:personal"
    )
    def personal(task, dry_run=False):
        from . import models

        for server in models.MailmanServer.objects.filter(
            personal_domain__isnull=False
        ):
            logger.info(f"Updating personal mailinglist on {server}")
            client = Client(server.url, server.username, server.password)
            domain = next(
                (d for d in client.domains if d.mail_host == server.personal_domain),
                None,
            )
            if not domain:
                logger.error(
                    f"Domain {server.personal_domain} not available on {server}."
                )
                continue
            mlist = next(
                (
                    li
                    for li in domain.lists
                    if li.list_name == settings.MAILINGLIST_PERSONAL_LIST
                ),
                None,
            )
            if not mlist:
                logger.info(
                    f"Creating new mailinglist {settings.MAILINGLIST_PERSONAL_LIST} on {server.personal_domain}"
                )
                mlist = domain.create_list(
                    settings.MAILINGLIST_PERSONAL_LIST,
                    style_name=settings.MAILINGLIST_LIST_STYLE,
                )
            for k, v in settings.MAILINGLIST_LIST_SETTINGS.items():
                logger.debug(f"Setting {k} to {v} on {mlist}")
                mlist.settings[k] = v
            mlist.settings["display_name"] = "Personal"
            mlist.settings["description"] = "Automatically managed list for personal"
            mlist.settings.save()
            existing = set((m.email for m in mlist.members if m.email))
            proposed = set(
                (
                    p.email.lower()
                    for p in campusonline.Person.objects.filter(employed=True)
                    if p.email
                )
            )
            add = proposed - existing
            remove = existing - proposed
            for email in add:
                logger.debug(f"Subscribing {email} to {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.subscribe(
                        email,
                        pre_verified=True,
                        pre_confirmed=True,
                        pre_approved=True,
                        invitation=False,
                    )
            for email in remove:
                logger.debug(f"Unsubscribing {email} from {mlist.fqdn_listname}")
                if not dry_run:
                    mlist.unsubscribe(email)
