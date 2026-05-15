from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AuditLog
from .services import create_audit_log


class AuditLogTests(TestCase):
    def test_create_audit_log_creates_record(self):
        user = get_user_model().objects.create_user(
            email='audit@example.com',
            username='audituser',
            password='StrongPassword123',
        )

        create_audit_log(user=user, event_type='test_event', object_type='unit', object_id='1')

        self.assertTrue(AuditLog.objects.filter(event_type='test_event', user=user).exists())

    def test_audit_log_handles_unexpected_metadata(self):
        create_audit_log(event_type='test_event', metadata='unexpected')

        self.assertEqual(AuditLog.objects.get().metadata, {'value': 'unexpected'})
