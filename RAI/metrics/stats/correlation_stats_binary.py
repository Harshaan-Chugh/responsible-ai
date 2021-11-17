from RAI.metrics.metric_group import MetricGroup
import math
import numpy as np
import scipy.stats

# Move config to external .json? 
_config = {
    "name": "correlation_stats_binary",
    "compatibility": {"type_restriction": "classification", "output_restriction": None},
    "dependency_list": [],
    "tags": ["stats"],
    "complexity_class": "linear",
    "metrics": {
        "point-biserial-r": {
            "display_name": "Point Biserial Coefficient",
            "type": "numeric",
            "has_range": False,
            "range": None,
            "explanation": "Mean is the expected value of data.",
        },
    }
}

# Type (Regression, Classification, Data | probability, numeric)


class BinaryCorrelationStats(MetricGroup, config=_config):
    compatibility = {"type_restriction": "binary_classification", "output_restriction": None}

    def __init__(self, ai_system) -> None:
        super().__init__(ai_system)
        
    def update(self, data):
        pass

    def compute(self, data_dict):
        if "data" in data_dict:
            args = {}
            if self.ai_system.user_config is not None and "stats" in self.ai_system.user_config and "args" in self.ai_system.user_config["stats"]:
                args = self.ai_system.user_config["stats"]["args"]

            data = data_dict["data"]
            self.metrics["point-biserial-r"].value = _calculate_per_feature(scipy.stats.pointbiserialr, data.X, data.y)


def _calculate_per_feature(function, X, y):
    result = []
    for i in range(np.shape(X)[1]):
        result.append(function(X[:, i], y))
    return result