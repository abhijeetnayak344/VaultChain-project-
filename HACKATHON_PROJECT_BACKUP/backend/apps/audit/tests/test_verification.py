from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.audit.models import AuditLog, IntegrityAlert, IntegrityCheck
from apps.audit.verification import STATUS_ALERT, STATUS_NOT_ANCHORED, STATUS_UNAVAILABLE, STATUS_VERIFIED, classify_integrity


class ClassifyIntegrityTests(SimpleTestCase):
    def test_match_is_verified(self):
        result = classify_integrity(
            current_hash="aaa",
            stored_hash="aaa",
            chain_hash="aaa",
            anchored=True,
            fabric_enabled=True,
            fabric_reachable=True,
        )
        self.assertEqual(result["status"], STATUS_VERIFIED)
        self.assertTrue(result["matches"])

    def test_blockchain_mismatch_is_security_alert(self):
        result = classify_integrity(
            current_hash="aaa",
            stored_hash="aaa",
            chain_hash="bbb",
            anchored=True,
            fabric_enabled=True,
            fabric_reachable=True,
        )
        self.assertEqual(result["status"], STATUS_ALERT)
        self.assertEqual(result["reason"], "blockchain_hash_mismatch")
        self.assertFalse(result["matches"])

    def test_local_tamper_is_security_alert_even_without_fabric(self):
        result = classify_integrity(
            current_hash="now",
            stored_hash="was",
            chain_hash="",
            anchored=False,
            fabric_enabled=False,
            fabric_reachable=False,
        )
        self.assertEqual(result["status"], STATUS_ALERT)
        self.assertEqual(result["reason"], "local_hash_mismatch")

    def test_missing_chain_hash_is_not_anchored(self):
        result = classify_integrity(
            current_hash="aaa",
            stored_hash="aaa",
            chain_hash="",
            anchored=False,
            fabric_enabled=True,
            fabric_reachable=True,
        )
        self.assertEqual(result["status"], STATUS_NOT_ANCHORED)

    def test_fabric_down_is_unavailable(self):
        result = classify_integrity(
            current_hash="aaa",
            stored_hash="aaa",
            chain_hash="",
            anchored=False,
            fabric_enabled=True,
            fabric_reachable=False,
        )
        self.assertEqual(result["status"], STATUS_UNAVAILABLE)


@override_settings(FABRIC_ENABLED=True, FABRIC_ANCHOR_URL="http://fabric.test")
class VerifyAndPersistTests(TestCase):
    def setUp(self):
        self.log = AuditLog.objects.create(
            actor_email="dcim-admin@aicte.gov.in",
            action=AuditLog.Action.SERVER_UPDATE,
            resource_type=AuditLog.ResourceType.SERVER,
            resource_id="srv-1",
            ip_address="10.20.1.40",
            details={"outcome": "success"},
            created_at=timezone.now(),
        )

    def test_mismatch_opens_security_alert(self):
        from unittest.mock import patch

        from apps.audit.blockchain import event_hash
        from apps.audit.verification import verify_and_record

        digest = event_hash(self.log)
        AuditLog.objects.filter(pk=self.log.pk).update(integrity_hash=digest, chain_status="anchored", chain_tx_id="tx-1")
        self.log.refresh_from_db()

        with patch("apps.audit.verification.fetch_chain_integrity") as fetch:
            fetch.return_value = {
                "fabric_enabled": True,
                "fabric_reachable": True,
                "anchored": True,
                "onChainHash": "0" * 64,
                "txId": "tx-1",
                "raw": {},
            }
            payload = verify_and_record(self.log)

        self.assertEqual(payload["status"], STATUS_ALERT)
        self.log.refresh_from_db()
        self.assertEqual(self.log.verification_status, STATUS_ALERT)
        self.assertTrue(IntegrityAlert.objects.filter(audit_log=self.log, status=IntegrityAlert.Status.OPEN).exists())
        self.assertEqual(IntegrityCheck.objects.filter(audit_log=self.log, result=STATUS_ALERT).count(), 1)

    def test_match_is_verified_and_does_not_alert(self):
        from unittest.mock import patch

        from apps.audit.blockchain import event_hash
        from apps.audit.verification import verify_and_record

        digest = event_hash(self.log)
        AuditLog.objects.filter(pk=self.log.pk).update(integrity_hash=digest, chain_status="anchored", chain_tx_id="tx-2")
        self.log.refresh_from_db()

        with patch("apps.audit.verification.fetch_chain_integrity") as fetch:
            fetch.return_value = {
                "fabric_enabled": True,
                "fabric_reachable": True,
                "anchored": True,
                "onChainHash": digest,
                "txId": "tx-2",
                "raw": {},
            }
            payload = verify_and_record(self.log)

        self.assertEqual(payload["status"], STATUS_VERIFIED)
        self.log.refresh_from_db()
        self.assertEqual(self.log.verification_status, STATUS_VERIFIED)
        self.assertFalse(IntegrityAlert.objects.filter(audit_log=self.log, status=IntegrityAlert.Status.OPEN).exists())
