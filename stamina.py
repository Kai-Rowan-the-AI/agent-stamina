"""Agent Stamina - Monitor endurance over long-horizon tasks."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import sqlite3
import json
import time


@dataclass
class StaminaSnapshot:
    """A single stamina measurement."""
    timestamp: datetime
    session_id: str
    
    # Core metrics (0.0 - 1.0)
    context_health: float  # % context window effectively used
    memory_freshness: float  # % memories from last hour
    error_rate: float  # errors per tool call
    repetition_score: float  # cycles of repetition detected
    
    # Derived
    overall_score: float = field(init=False)
    
    def __post_init__(self):
        # Weighted composite score
        weights = {
            'context_health': 0.35,
            'memory_freshness': 0.25,
            'error_rate': 0.25,  # inverted - lower is better
            'repetition_score': 0.15  # inverted
        }
        self.overall_score = (
            self.context_health * weights['context_health'] +
            self.memory_freshness * weights['memory_freshness'] +
            (1 - self.error_rate) * weights['error_rate'] +
            (1 - self.repetition_score) * weights['repetition_score']
        ) * 100
    
    def status(self) -> str:
        if self.overall_score >= 70:
            return "healthy"
        elif self.overall_score >= 40:
            return "degraded"
        else:
            return "critical"


class StaminaMonitor:
    """Monitor agent stamina over a session."""
    
    def __init__(self, session_id: str, db_path: str = ".agent_stamina.db"):
        self.session_id = session_id
        self.db_path = db_path
        self.start_time = datetime.now()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite storage."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stamina_snapshots (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                context_health REAL,
                memory_freshness REAL,
                error_rate REAL,
                repetition_score REAL,
                overall_score REAL
            )
        """)
        conn.commit()
        conn.close()
    
    def record(self, 
               context_health: float,
               memory_freshness: float,
               error_rate: float,
               repetition_score: float) -> StaminaSnapshot:
        """Record a stamina snapshot."""
        snapshot = StaminaSnapshot(
            timestamp=datetime.now(),
            session_id=self.session_id,
            context_health=context_health,
            memory_freshness=memory_freshness,
            error_rate=error_rate,
            repetition_score=repetition_score
        )
        
        # Store
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO stamina_snapshots 
            (session_id, timestamp, context_health, memory_freshness, 
             error_rate, repetition_score, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.session_id,
            snapshot.timestamp.isoformat(),
            snapshot.context_health,
            snapshot.memory_freshness,
            snapshot.error_rate,
            snapshot.repetition_score,
            snapshot.overall_score
        ))
        conn.commit()
        conn.close()
        
        return snapshot
    
    def get_history(self, minutes: int = 60) -> List[StaminaSnapshot]:
        """Get stamina history for session."""
        since = datetime.now() - timedelta(minutes=minutes)
        
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT timestamp, context_health, memory_freshness,
                   error_rate, repetition_score
            FROM stamina_snapshots
            WHERE session_id = ? AND timestamp > ?
            ORDER BY timestamp
        """, (self.session_id, since.isoformat())).fetchall()
        conn.close()
        
        return [
            StaminaSnapshot(
                timestamp=datetime.fromisoformat(row[0]),
                session_id=self.session_id,
                context_health=row[1],
                memory_freshness=row[2],
                error_rate=row[3],
                repetition_score=row[4]
            )
            for row in rows
        ]
    
    def current_status(self) -> Optional[StaminaSnapshot]:
        """Get most recent stamina snapshot."""
        history = self.get_history(minutes=999999)  # All time
        return history[-1] if history else None
    
    def should_checkpoint(self) -> bool:
        """Recommend whether to checkpoint now."""
        status = self.current_status()
        if not status:
            return False
        
        # Checkpoint if degraded or critical
        return status.status() in ("degraded", "critical")
    
    def generate_report(self) -> Dict:
        """Generate session stamina report."""
        history = self.get_history(minutes=999999)
        if not history:
            return {"error": "No data recorded"}
        
        scores = [h.overall_score for h in history]
        
        return {
            "session_id": self.session_id,
            "duration_minutes": (datetime.now() - self.start_time).seconds / 60,
            "snapshots_count": len(history),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "current_status": history[-1].status(),
            "recommendation": self._get_recommendation(history[-1])
        }
    
    def _get_recommendation(self, snapshot: StaminaSnapshot) -> str:
        """Get recommendation based on current state."""
        if snapshot.status() == "critical":
            return "STOP: Context severely degraded. Checkpoint immediately."
        elif snapshot.status() == "degraded":
            return "CAUTION: Consider checkpointing or refreshing context."
        elif snapshot.memory_freshness < 0.4:
            return "WATCH: Memories becoming stale. Review recent context."
        else:
            return "GOOD: Proceed with confidence."
