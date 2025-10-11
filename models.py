from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

class EventType(Enum):
    """Security event types"""
    FAILED_LOGIN = "failed_login"
    SUCCESSFUL_LOGIN = "successful_login"
    MALWARE_DETECTED = "malware_detected"
    FIREWALL_BLOCK = "firewall_block"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SUSPICIOUS_CONNECTION = "suspicious_connection"

class SeverityLevel(Enum):
    """Event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class SecurityEvent:
    """Security event data model"""
    event_id: str
    timestamp: datetime
    event_type: EventType
    source_ip: str
    destination_ip: str
    user: str
    severity: SeverityLevel
    country: str
    message: str
    risk_score: int
    bytes_sent: int
    bytes_received: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.event_id,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'event_type': self.event_type.value,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'user': self.user,
            'severity': self.severity.value,
            'country': self.country,
            'message': self.message,
            'risk_score': self.risk_score,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received
        }

@dataclass
class QueryResult:
    """Query result container"""
    success: bool
    query: str
    parsed_query: Dict[str, Any]
    results: Dict[str, Any]
    processing_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'query': self.query,
            'parsed_query': self.parsed_query,
            'results': self.results,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class ChartConfig:
    """Chart configuration"""
    type: str
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'title': self.title,
            'data': self.data,
            'options': self.options
        }