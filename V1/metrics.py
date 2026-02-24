import asyncio
from datetime import datetime
import pyodbc
import os
import sys
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | Line:%(lineno)d | %(message)s'
)
local_logger = logging.getLogger(__name__)

local_logger.debug(f"Starting BerthMetricCalculator.")

class BerthMetricCalculator:
    def __init__(self, start_index=0, end_index=1585, last_bollard=81, bollard_spacing=20):
        self.start_index = start_index
        self.end_index = end_index
        self.last_bollard = last_bollard
        self.bollard_spacing = bollard_spacing
        self.berth_map = {}
        self._generate_berth_map()

    def _generate_berth_map(self):
        bollard = self.last_bollard
        for idx in range(self.end_index, self.start_index, -self.bollard_spacing):
            self.berth_map[f"B{bollard}"] = idx
            bollard -= 1

    def __generate_real_metrics(self, planned_bollard: str, loa: float, is_starboard: bool):
        metrics = planned_bollard.split(".")
        base = metrics[0].strip().upper()
        offset = int(metrics[1]) * 2 if len(metrics) > 1 else 0

        if base not in self.berth_map:
            local_logger.error(f"Unknown bollard: {base}")
            raise ValueError(f"Unknown bollard: {base}")

        fore = self.berth_map[base] + offset
        aft = fore + loa if is_starboard else fore - loa

        # local_logger.info(f"[Real] plannedBollard: {planned_bollard}, fore_metric_point: {fore}, aft_metric_point: {aft}")
        real = True
        return (round(fore, 2), round(aft, 2), real)

    def __generate_mock_metrics(self, loa: float, is_starboard: bool):
        if is_starboard:
            fore = self.end_index - loa
            aft = self.end_index
        else:
            fore = self.end_index
            aft = self.end_index - loa

        # local_logger.info(f"[Mock] plannedBollard: None, fore_metric_point: {fore}, aft_metric_point: {aft}")
        real = False
        return (round(fore, 2), round(aft, 2), real)

    def get_metrics(self, planned_bollard: str, loa: float, is_starboard: bool):
        if isinstance(planned_bollard, str) and planned_bollard.strip().upper().startswith("B"):
            return self.__generate_real_metrics(planned_bollard, loa, is_starboard)
        return self.__generate_mock_metrics(loa, is_starboard)

    def __repr__(self):
        return f"<BerthMetricCalculator: {len(self.berth_map)} bollards mapped>"

