"""
Shared Schemas
Defines data formats for frames, detections, and violations.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Frame:
    frame_id: int
    # image: bytes or str (base64-encoded)
    timestamp: Optional[float] = None

@dataclass
class DetectionResult:
    frame_id: int
    detections: List[dict]  # e.g., [{"label": str, "bbox": [x1, y1, x2, y2], "score": float}]
    violations: List[dict]  # e.g., [{"roi_id": int, "type": str}]

@dataclass
class ViolationEvent:
    frame_id: int
    roi_id: int
    violation_type: str
    timestamp: Optional[float] = None
