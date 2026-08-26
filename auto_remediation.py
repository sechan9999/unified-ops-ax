"""Durable Auto-Remediation Engine for Unified Ops AX.

Provides atomic policy state overrides, priority precedence (DLP > Latency > Cost),
replay protection, webhook idempotency deduplication, and structured audit logging.
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("auto_remediation")


class AnomalyType(Enum):
    COST_SPIKE = "cost_spike"
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_SURGE = "error_rate_surge"
    DLP_BURST = "dlp_burst"
    TOKEN_OVERRUN = "token_overrun"


class PolicyPriority(Enum):
    CRITICAL = 3  # DLP_BURST
    HIGH = 2      # LATENCY_SPIKE / ERROR_RATE_SURGE
    NORMAL = 1    # COST_SPIKE / TOKEN_OVERRUN


@dataclass
class RemediationPolicy:
    anomaly_type: AnomalyType
    trigger_threshold: float
    actions: List[str]
    priority: PolicyPriority = PolicyPriority.NORMAL
    fallback_model: Optional[str] = None
    cost_weight_boost: float = 0.0
    quality_weight_cut: float = 0.0
    cooldown_sec: int = 300


@dataclass
class PolicyOverrideState:
    active_policy: RemediationPolicy
    override_id: str
    owner: str
    version: str
    applied_at: float
    expires_at: float
    baseline_weights: Dict[str, float]
    active_weights: Dict[str, float]
    rollback_token: str


class DurablePolicyEngine:
    """Stateful, atomic policy engine managing overrides, precedence, and idempotency."""

    PRIORITY_MAP = {
        AnomalyType.DLP_BURST: PolicyPriority.CRITICAL,
        AnomalyType.LATENCY_SPIKE: PolicyPriority.HIGH,
        AnomalyType.ERROR_RATE_SURGE: PolicyPriority.HIGH,
        AnomalyType.COST_SPIKE: PolicyPriority.NORMAL,
        AnomalyType.TOKEN_OVERRUN: PolicyPriority.NORMAL,
    }

    def __init__(self, webhook_secret: str = "unified-ops-webhook-secret"):
        self.webhook_secret = webhook_secret
        self.active_override: Optional[PolicyOverrideState] = None
        self.processed_alert_ids: set = set()
        self.audit_logs: List[Dict[str, Any]] = []
        self.baseline_router_weights = {
            "quality_weight": 0.5,
            "cost_weight": 0.3,
            "latency_weight": 0.2
        }
        self.policies = {
            AnomalyType.COST_SPIKE: RemediationPolicy(
                anomaly_type=AnomalyType.COST_SPIKE,
                trigger_threshold=5.0,
                priority=PolicyPriority.NORMAL,
                actions=["switch_to_cheaper_model", "enable_caching", "notify_admin"],
                fallback_model="gemini-3.5-flash",
                cost_weight_boost=0.3,
                cooldown_sec=300
            ),
            AnomalyType.LATENCY_SPIKE: RemediationPolicy(
                anomaly_type=AnomalyType.LATENCY_SPIKE,
                trigger_threshold=5000.0,
                priority=PolicyPriority.HIGH,
                actions=["scale_k8s_pods", "switch_to_faster_model", "notify_ops"],
                fallback_model="gemini-2.0-flash",
                cooldown_sec=300
            ),
            AnomalyType.DLP_BURST: RemediationPolicy(
                anomaly_type=AnomalyType.DLP_BURST,
                trigger_threshold=10.0,
                priority=PolicyPriority.CRITICAL,
                actions=["escalate_dlp_strictness", "block_violating_ips", "alert_security"],
                cooldown_sec=600
            )
        }

    def validate_webhook(self, alert_id: str, timestamp: float, max_age_sec: float = 300.0) -> Tuple[bool, str]:
        """Validates timestamp replay protection and alert_id idempotency."""
        now = time.time()
        if abs(now - timestamp) > max_age_sec:
            return False, f"Replay rejected: timestamp delta {abs(now - timestamp):.1f}s exceeds limit {max_age_sec}s"
        
        if alert_id in self.processed_alert_ids:
            return False, f"Idempotency rejected: alert_id {alert_id} already processed"

        return True, "valid"

    def apply_remediation(
        self,
        anomaly_type: AnomalyType,
        metric_value: float,
        alert_id: Optional[str] = None,
        timestamp: Optional[float] = None,
        owner: str = "auto_remediator"
    ) -> Dict[str, Any]:
        """Executes atomic remediation with precedence ordering and structured audit logging."""
        t_now = timestamp or time.time()
        a_id = alert_id or f"alert_{int(t_now * 1000)}_{anomaly_type.value}"

        # 1. Validate webhook & idempotency
        valid, msg = self.validate_webhook(a_id, t_now)
        if not valid:
            logger.warning(f"[IDEMPOTENCY_REJECTED] {msg}")
            return {
                "success": False,
                "status": "rejected",
                "reason": msg,
                "alert_id": a_id
            }

        policy = self.policies.get(anomaly_type)
        if not policy:
            return {"success": False, "status": "no_policy", "anomaly_type": anomaly_type.value}

        # 2. Precedence check: don't let lower priority policy overwrite a higher priority active override
        incoming_priority = self.PRIORITY_MAP.get(anomaly_type, PolicyPriority.NORMAL)
        if self.active_override and time.time() < self.active_override.expires_at:
            active_priority = self.active_override.active_policy.priority
            if incoming_priority.value < active_priority.value:
                reason = f"Precedence rejected: incoming {anomaly_type.value} (P{incoming_priority.value}) < active {self.active_override.active_policy.anomaly_type.value} (P{active_priority.value})"
                logger.warning(f"[PRECEDENCE_BLOCKED] {reason}")
                return {
                    "success": False,
                    "status": "precedence_blocked",
                    "reason": reason,
                    "active_policy": self.active_override.active_policy.anomaly_type.value
                }

        # 3. Calculate new weights atomically
        new_weights = dict(self.baseline_router_weights)
        if policy.cost_weight_boost > 0:
            new_weights["cost_weight"] += policy.cost_weight_boost
            new_weights["quality_weight"] = max(0.1, new_weights["quality_weight"] - policy.cost_weight_boost)

        rollback_token = hashlib.sha256(f"{a_id}_{t_now}".encode()).hexdigest()[:12]
        
        override = PolicyOverrideState(
            active_policy=policy,
            override_id=a_id,
            owner=owner,
            version="1.2.0",
            applied_at=t_now,
            expires_at=t_now + policy.cooldown_sec,
            baseline_weights=dict(self.baseline_router_weights),
            active_weights=new_weights,
            rollback_token=rollback_token
        )

        self.active_override = override
        self.processed_alert_ids.add(a_id)

        audit_entry = {
            "timestamp": t_now,
            "alert_id": a_id,
            "anomaly_type": anomaly_type.value,
            "metric_value": metric_value,
            "priority": incoming_priority.name,
            "actions_applied": policy.actions,
            "fallback_model": policy.fallback_model,
            "rollback_token": rollback_token,
            "expires_at": override.expires_at
        }
        self.audit_logs.append(audit_entry)

        logger.info(f"[POLICY_APPLIED] {anomaly_type.value} (Priority: {incoming_priority.name}) -> Token: {rollback_token}")

        return {
            "success": True,
            "status": "policy_applied",
            "alert_id": a_id,
            "anomaly_type": anomaly_type.value,
            "priority": incoming_priority.name,
            "actions": policy.actions,
            "fallback_model": policy.fallback_model,
            "active_weights": new_weights,
            "rollback_token": rollback_token,
            "cooldown_sec": policy.cooldown_sec
        }

    def rollback_override(self, rollback_token: str) -> Dict[str, Any]:
        """Manually rolls back an active policy override using a rollback token."""
        if not self.active_override:
            return {"success": False, "reason": "No active policy override found"}

        if self.active_override.rollback_token != rollback_token:
            return {"success": False, "reason": "Invalid rollback token"}

        prev_policy = self.active_override.active_policy.anomaly_type.value
        self.active_override = None
        logger.info(f"[POLICY_ROLLED_BACK] Restored baseline weights for previous override {prev_policy}")
        return {
            "success": True,
            "status": "rolled_back",
            "previous_policy": prev_policy,
            "restored_weights": self.baseline_router_weights
        }

    def get_status(self) -> Dict[str, Any]:
        is_active = self.active_override is not None and time.time() < self.active_override.expires_at
        return {
            "active_override": {
                "policy": self.active_override.active_policy.anomaly_type.value,
                "owner": self.active_override.owner,
                "applied_at": self.active_override.applied_at,
                "expires_at": self.active_override.expires_at,
                "rollback_token": self.active_override.rollback_token,
                "active_weights": self.active_override.active_weights
            } if is_active else None,
            "total_audits": len(self.audit_logs),
            "processed_alert_count": len(self.processed_alert_ids)
        }
