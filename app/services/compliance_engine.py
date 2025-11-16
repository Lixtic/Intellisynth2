from typing import List, Any

class ComplianceRule:
    """
    Base class for compliance rules. Each rule should implement the check method.
    """
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def check(self, log_entry: Any) -> bool:
        """
        Returns True if log_entry passes the rule, False if it violates.
        Override this method in subclasses.
        """
        raise NotImplementedError("Each rule must implement the check method.")


class ComplianceEngine:
    def __init__(self, rules: List[ComplianceRule]):
        self.rules = rules

    def evaluate(self, log_entry: Any) -> List[ComplianceRule]:
        """
        Returns a list of rules that were violated by the log_entry.
        """
        violations = []
        for rule in self.rules:
            try:
                if not rule.check(log_entry):
                    violations.append(rule)
            except Exception as e:
                # Optionally log or handle rule evaluation errors
                violations.append(rule)
        return violations
