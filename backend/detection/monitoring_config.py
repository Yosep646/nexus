"""Configuration for bounded camera analysis."""
from dataclasses import dataclass

@dataclass(frozen=True)
class MonitoringConfig:
    interval_seconds: int = 15
    max_concurrent_cameras: int = 2
    frame_timeout_seconds: int = 25

    def validate(self):
        if self.interval_seconds < 5:
            raise ValueError('Interval must be at least five seconds')
        if not 1 <= self.max_concurrent_cameras <= 16:
            raise ValueError('Invalid concurrency limit')
        if self.frame_timeout_seconds < 1:
            raise ValueError('Invalid frame timeout')
        return self
