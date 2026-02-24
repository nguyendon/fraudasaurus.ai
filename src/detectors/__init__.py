"""Fraud detection modules."""

from .structuring import StructuringDetector
from .account_takeover import AccountTakeoverDetector
from .kiting import KitingDetector
from .dormant import DormantAccountDetector
from .anomaly import AnomalyDetector

ALL_DETECTORS = [
    StructuringDetector,
    AccountTakeoverDetector,
    KitingDetector,
    DormantAccountDetector,
    AnomalyDetector,
]
