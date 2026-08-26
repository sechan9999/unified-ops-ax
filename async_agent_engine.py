"""Asynchronous Agent Execution Engine for Unified Ops AX.

Manages background worker pools, priority job queues, latency percentile metrics (p50, p95, p99),
stream ingestion, and durable policy remediations.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple

from auto_remediation import AnomalyType, DurablePolicyEngine
from k8s_hpa_autoscaler import K8sHPAAutoscaler
from local_dlp_guardrail import LocalDLPGuardrail
from pubsub_kafka_stream_processor import StreamIngestManager
from splunk_telemetry import get_telemetry

logger = logging.getLogger("async_agent_engine")


class TaskPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REMEDIATING = "remediating"


@dataclass
class AgentTask:
    task_id: str
    name: str
    func: Callable
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    remediation_applied: Optional[Dict[str, Any]] = None


class AsyncAgentEngine:
    """Multi-worker asynchronous background agent execution engine."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.tasks: Dict[str, AgentTask] = {}
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        self.start_time: Optional[float] = None
        self.total_processed = 0
        self.total_remediations = 0
        self.latencies_ms: List[float] = []

        # Subsystems
        self.telemetry: SplunkTelemetryEmitter = get_telemetry()
        self.policy_engine = DurablePolicyEngine()
        self.k8s_autoscaler = K8sHPAAutoscaler()
        self.dlp_guardrail = LocalDLPGuardrail()
        self.stream_manager = StreamIngestManager(agent_engine=self)

    async def start(self):
        """Starts worker pool threads."""
        if self.is_running:
            return
        self.is_running = True
        self.start_time = time.time()
        self.workers = [
            asyncio.create_task(self._worker_loop(w_id))
            for w_id in range(self.num_workers)
        ]
        logger.info(f"AsyncAgentEngine started with {self.num_workers} worker threads.")

    async def stop(self):
        """Stops background workers gracefully."""
        self.is_running = False
        for w in self.workers:
            w.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        logger.info("AsyncAgentEngine stopped.")

    async def submit_task(
        self,
        func: Callable,
        *args,
        name: str = "agent_task",
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs
    ) -> AgentTask:
        """Enqueues a task into the priority queue."""
        t_id = f"task_{int(time.time() * 1000)}_{len(self.tasks) + 1}"
        task = AgentTask(
            task_id=t_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        self.tasks[t_id] = task
        await self.task_queue.put((priority.value, task.created_at, task.task_id, task))
        logger.info(f"Task {t_id} ({name}) enqueued with priority {priority.name}")
        return task

    async def trigger_anomaly_remediation(self, anomaly_type: AnomalyType, metric_value: float) -> Dict[str, Any]:
        """Triggers an event-driven background remediation policy with precedence checks."""
        rem_id = f"rem_{int(time.time() * 1000)}"
        remediation_task = AgentTask(
            task_id=rem_id,
            name=f"remediation_{anomaly_type.value}",
            func=lambda: None,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.REMEDIATING
        )
        self.tasks[rem_id] = remediation_task
        remediation_task.started_at = time.time()

        res = self.policy_engine.apply_remediation(anomaly_type, metric_value)
        res["handled"] = True

        # K8s HPA scale-out trigger on latency spike
        if anomaly_type in (AnomalyType.LATENCY_SPIKE, "latency_spike"):
            k8s_res = self.k8s_autoscaler.trigger_latency_scaleout(metric_value)
            res["k8s_autoscaling"] = k8s_res

        remediation_task.status = TaskStatus.COMPLETED
        remediation_task.completed_at = time.time()
        remediation_task.duration_ms = round((remediation_task.completed_at - remediation_task.started_at) * 1000, 2)
        remediation_task.result = res
        remediation_task.remediation_applied = res

        self.total_remediations += 1
        self.latencies_ms.append(remediation_task.duration_ms)

        self.telemetry.emit_anomaly(
            anomaly_type=anomaly_type.value if isinstance(anomaly_type, AnomalyType) else str(anomaly_type),
            metric_name="background_remediation",
            current_value=metric_value,
            threshold=5.0,
            remediation_triggered=True
        )
        return res

    async def _worker_loop(self, worker_id: int):
        """Worker loop executing tasks from the priority queue."""
        while self.is_running:
            try:
                p_val, t_time, t_id, task = await asyncio.wait_for(self.task_queue.get(), timeout=0.5)
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

                try:
                    if asyncio.iscoroutinefunction(task.func):
                        res = await task.func(*task.args, **task.kwargs)
                    else:
                        res = await asyncio.to_thread(task.func, *task.args, **task.kwargs)

                    task.result = res
                    task.status = TaskStatus.COMPLETED
                    self.total_processed += 1
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    logger.error(f"Worker-{worker_id} Task {task.name} failed: {e}")
                finally:
                    task.completed_at = time.time()
                    task.duration_ms = round((task.completed_at - task.started_at) * 1000, 2)
                    self.latencies_ms.append(task.duration_ms)
                    self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker-{worker_id} unexpected error: {e}")

    def _calc_percentile(self, percentile: float) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_l = sorted(self.latencies_ms)
        k = (len(sorted_l) - 1) * (percentile / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_l) else f
        return round(sorted_l[f] + (k - f) * (sorted_l[c] - sorted_l[f]), 2)

    def get_status(self) -> Dict[str, Any]:
        """Returns engine status, background statistics, and latency percentiles (p50, p95, p99)."""
        pending_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        running_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        completed_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        uptime_sec = round(time.time() - self.start_time, 2) if self.start_time else 0.0
        throughput = round(self.total_processed / uptime_sec, 2) if uptime_sec > 0 else 0.0
        active_workers = sum(1 for w in self.workers if not w.done()) if self.workers else 0

        return {
            "is_running": self.is_running and active_workers > 0,
            "active_workers": active_workers,
            "num_workers": self.num_workers,
            "uptime_sec": uptime_sec,
            "throughput_tasks_per_sec": throughput,
            "total_tasks": len(self.tasks),
            "total_processed": self.total_processed,
            "total_remediations": self.total_remediations,
            "percentile_latencies_ms": {
                "p50": self._calc_percentile(50.0),
                "p95": self._calc_percentile(95.0),
                "p99": self._calc_percentile(99.0)
            },
            "policy_engine": self.policy_engine.get_status(),
            "streaming_ingest": self.stream_manager.get_stats(),
            "k8s_autoscaling": self.k8s_autoscaler.get_stats(),
            "local_dlp": self.dlp_guardrail.get_stats(),
            "counts": {
                "pending": pending_count,
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count
            }
        }
