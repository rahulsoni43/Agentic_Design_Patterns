"""
Data Collectors for Sherlock SRE

Collectors gather data from various sources (K8s, logs, metrics, etc.)
and convert them into standardized Event objects.
"""

from .base import BaseCollector
from .k8s_collector import K8sCollector

__all__ = ["BaseCollector", "K8sCollector"]
