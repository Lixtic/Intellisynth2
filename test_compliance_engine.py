#!/usr/bin/env python3
"""Simple harness to validate the ComplianceEngine behavior."""

from datetime import datetime, timezone
from typing import Iterable, List

from app.services.compliance_engine import ComplianceEngine, ComplianceRule


SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class RequiredFieldsRule(ComplianceRule):
    def __init__(self, required_fields: Iterable[str]):
        super().__init__(
            name="Required Fields Present",
            description="Ensures the log entry contains the core identifiers",
        )
        self.required_fields = tuple(required_fields)
        self.missing_fields: List[str] = []

    def check(self, log_entry):
        self.missing_fields = [
            field for field in self.required_fields if not log_entry.get(field)
        ]
        return len(self.missing_fields) == 0


class SeverityThresholdRule(ComplianceRule):
    def __init__(self, max_severity: str = "high"):
        super().__init__(
            name="Severity Threshold",
            description="Flags entries that exceed the allowed severity",
        )
        max_key = max_severity.lower()
        if max_key not in SEVERITY_RANK:
            raise ValueError(f"Unknown severity level: {max_severity}")
        self.max_severity = max_key

    def check(self, log_entry):
        severity = log_entry.get("severity", "info")
        severity_rank = SEVERITY_RANK.get(str(severity).lower(), 0)
        return severity_rank <= SEVERITY_RANK[self.max_severity]


class AllowedActionRule(ComplianceRule):
    def __init__(self, disallowed_actions: Iterable[str]):
        super().__init__(
            name="Allowed Actions",
            description="Blocks explicitly disallowed actions",
        )
        self.disallowed_actions = {action.lower() for action in disallowed_actions}

    def check(self, log_entry):
        action = str(log_entry.get("action_type", "")).lower()
        return action not in self.disallowed_actions


class FaultyRule(ComplianceRule):
    def __init__(self):
        super().__init__(
            name="Faulty Rule",
            description="Intentionally raises to validate error handling",
        )

    def check(self, _log_entry):
        raise RuntimeError("Intentional rule failure")


def run_scenario(name: str, engine: ComplianceEngine, log_entry, expected_violations: int):
    print(f"\n▶ Scenario: {name}")
    violations = engine.evaluate(log_entry)
    for violation in violations:
        detail = getattr(violation, "missing_fields", None)
        if detail:
            print(f"  - {violation.name}: missing {', '.join(detail)}")
        else:
            print(f"  - {violation.name}")

    assert len(violations) == expected_violations, (
        f"Expected {expected_violations} violation(s) but got {len(violations)}"
    )
    status = "PASSED" if expected_violations == 0 else "VIOLATIONS EXPECTED"
    print(f"   ✓ {status}")


def test_faulty_rule_handling():
    print("\n▶ Scenario: Faulty rule handling")
    engine = ComplianceEngine([FaultyRule()])
    violations = engine.evaluate({})
    assert len(violations) == 1, "Faulty rule should be reported as violation"
    print("   ✓ Faulty rule reported as violation")


def run_compliance_tests():
    print("\n=====================================================")
    print("  COMPLIANCE ENGINE TEST SUITE")
    print("=====================================================")

    rules = [
        RequiredFieldsRule(["agent_id", "action_type", "timestamp"]),
        SeverityThresholdRule(max_severity="high"),
        AllowedActionRule(["delete_logs", "disable_audit"]),
    ]
    engine = ComplianceEngine(rules)

    timestamp = datetime.now(timezone.utc).isoformat()

    run_scenario(
        "Fully compliant entry",
        engine,
        {
            "agent_id": "agent-42",
            "action_type": "update_config",
            "timestamp": timestamp,
            "severity": "medium",
        },
        expected_violations=0,
    )

    run_scenario(
        "Missing identifiers",
        engine,
        {
            "action_type": "update_config",
            "timestamp": timestamp,
            "severity": "medium",
        },
        expected_violations=1,
    )

    run_scenario(
        "Severity above threshold",
        engine,
        {
            "agent_id": "agent-11",
            "action_type": "rotate_keys",
            "timestamp": timestamp,
            "severity": "critical",
        },
        expected_violations=1,
    )

    run_scenario(
        "Disallowed action",
        engine,
        {
            "agent_id": "agent-7",
            "action_type": "delete_logs",
            "timestamp": timestamp,
            "severity": "low",
        },
        expected_violations=1,
    )

    run_scenario(
        "Multiple violations",
        engine,
        {
            "action_type": "disable_audit",
            "severity": "critical",
        },
        expected_violations=3,
    )

    test_faulty_rule_handling()

    print("\n=====================================================")
    print("  ✓ COMPLIANCE ENGINE TESTS COMPLETED")
    print("=====================================================\n")


if __name__ == "__main__":
    run_compliance_tests()
