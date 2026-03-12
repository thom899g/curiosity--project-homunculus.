"""
Event schema definitions for the Distributed Cognitive Core.
Ensures type safety and consistency across all services.
"""
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Event Types
class EventType(str, Enum):
    MEMORY_CREATED = "memory.created"
    MEMORY_VECTORIZED = "memory.vectorized"
    DECISION_REQUESTED = "decision.requested"
    DECISION_COMPLETED = "decision.completed"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"
    SYSTEM_HEALTH = "system.health"
    COGNITIVE_GAP_IDENTIFIED = "cognitive.gap.identified"

# Event Base Model
class BaseEvent(BaseModel):
    """Base event with common fields and validation."""
    event_type: EventType
    source_service: str
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('source_service')
    def validate_service(cls, v):
        valid_services = ['memory', 'decision', 'executor', 'watchdog', 'guardrail']
        if v not in valid_services:
            raise ValueError(f'Invalid service: {v}. Must be one of {valid_services}')
        return v
    
    class Config:
        use_enum_values = True

# Specific Event Models
class MemoryCreatedEvent(BaseEvent):
    """Emitted when a new memory is created."""
    event_type: EventType = EventType.MEMORY_CREATED
    
    @validator('payload')
    def validate_payload(cls, v):
        required = ['memory_id', 'memory_type', 'content']
        for field in required:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v

class DecisionRequestedEvent(BaseEvent):
    """Emitted when a decision is requested."""
    event_type: EventType = EventType.DECISION_REQUESTED
    
    @validator('payload')
    def validate_payload(cls, v):
        if 'query' not in v:
            raise ValueError('Missing required field: query')
        if 'context' not in v:
            raise ValueError('Missing required field: context')
        return v

class DecisionCompletedEvent(BaseEvent):
    """Emitted when a decision is completed."""
    event_type: EventType = EventType.DECISION_COMPLETED
    
    @validator('payload')
    def validate_payload(cls, v):
        required = ['decision_id', 'result', 'confidence', 'reasoning']
        for field in required:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v

class ActionExecutedEvent(BaseEvent):
    """Emitted when an action is successfully executed."""
    event_type: EventType = EventType.ACTION_EXECUTED
    
    @validator('payload')
    def validate_payload(cls, v):
        required = ['action_id', 'action_type', 'result']
        for field in required:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v

class SystemHealthEvent(BaseEvent):
    """Emitted for system health monitoring."""
    event_type: EventType = EventType.SYSTEM_HEALTH
    
    @validator('payload')
    def validate_payload(cls, v):
        required = ['service', 'status', 'metrics']
        for field in required:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v

# Event factory function
def create_event(
    event_type: EventType,
    source_service: str,
    payload: Dict[str, Any]
) -> BaseEvent:
    """Create a properly typed event based on event_type."""
    event_classes = {
        EventType.MEMORY_CREATED: MemoryCreatedEvent,
        EventType.DECISION_REQUESTED: DecisionRequestedEvent,
        EventType.DECISION_COMPLETED: DecisionCompletedEvent,
        EventType.ACTION_EXECUTED: ActionExecutedEvent,
        EventType.SYSTEM_HEALTH: SystemHealthEvent
    }
    
    if event_type in event_classes:
        return event_classes[event_type](
            source_service=source_service,
            payload=payload
        )
    
    # For other event types, use base event
    return BaseEvent(
        event_type=event_type,
        source_service=source_service,
        payload=payload
    )