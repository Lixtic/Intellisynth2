"""Firestore-backed storage helpers for compliance rules."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Union
import logging

from app.firebase_config import Collections
from app.models.compliance_rule import ComplianceRule
from app.services.firebase_service import FirestoreService

logger = logging.getLogger(__name__)

RulePayload = Union[ComplianceRule, Dict[str, Any]]


class ComplianceRuleFirestoreService(FirestoreService[Dict[str, Any]]):
    """Persists compliance rules to Firestore for shared storage."""

    def __init__(self) -> None:
        super().__init__(Collections.COMPLIANCE_RULES)

    async def sync_rule(self, rule: RulePayload) -> bool:
        """Create or update a single compliance rule document."""
        if not self._is_ready():
            return False

        try:
            payload = self._normalize(rule)
            rule_id = payload["id"]

            if await self.exists(rule_id):
                await self.update(rule_id, payload)
            else:
                await self.create(rule_id, payload)
            return True
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to sync compliance rule to Firestore: %s", exc)
            return False

    async def sync_rules(self, rules: Iterable[RulePayload]) -> None:
        """Bulk upsert convenience method."""
        if not self._is_ready():
            return

        for rule in rules:
            await self.sync_rule(rule)

    async def delete_rule(self, rule_id: str) -> bool:
        """Remove a rule document from Firestore."""
        if not self._is_ready():
            return False
        try:
            return await self.delete(rule_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to delete compliance rule from Firestore: %s", exc)
            return False

    def _normalize(self, rule: RulePayload) -> Dict[str, Any]:
        if isinstance(rule, ComplianceRule):
            data = rule.to_dict()
        else:
            data = dict(rule)

        if not data.get("id"):
            raise ValueError("Compliance rule payload must include an 'id'")

        # Firestore prefers naive dictionaries; ensure primitives where possible.
        normalized: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                normalized[key] = value.isoformat()
            else:
                normalized[key] = value

        normalized.setdefault("last_synced_at", datetime.utcnow().isoformat())
        return normalized

    def _is_ready(self) -> bool:
        """Best-effort guard to prevent crashes when Firebase isn't configured."""
        try:
            _ = self.collection
            return True
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Firestore not ready for compliance rules: %s", exc)
            return False


compliance_rule_firestore_service = ComplianceRuleFirestoreService()
