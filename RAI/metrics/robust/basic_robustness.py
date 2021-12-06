from RAI.metrics.metric_group import MetricGroup
import math
import numpy as np


# Move config to external .json? 
_config = {
    "name" : "basic_robustness",
    "compatibility": {"type_restriction": None, "output_restriction": None},
    "dependency_list": [],
    "tags": ["robustness", "Normalization"],
    "complexity_class": "linear",
    "metrics": {
        "normalized_feature_01": {
            "display_name": "Normalized Features 0-1",
            "type": "boolean",
            "has_range": False,
            "range": [None, None],
            "explanation": "Whether of not each training feature is normalized to 0/1.",
        },
        "normalized_feature_std": {
            "display_name": "Normalized Features Standard",
            "type": "boolean",
            "has_range": False,
            "range": [None, None],
            "explanation": "Whether of not each training feature is normalized to standard.",
        }, 
    }
}

# Type (Regression, Classification, Data | probability, numeric)


class BasicRobustMetricGroup(MetricGroup, config = _config):
     
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

            # masked_data = np.ma.masked_array(data, self.ai_system.meta_database.scalar_mask)
            mask = np.zeros_like(data.X)
            mask = mask + self.ai_system.meta_database.scalar_mask
            masked_data = np.ma.masked_array(data.X, mask)

            mean_v = np.mean(masked_data, **args.get("mean", {}), axis=0, keepdims=True)
            std_v = np.std(masked_data, **args.get("covariance", {}), axis=0, keepdims= True )
            max_v = np.max(masked_data, axis=0, keepdims=True)
            min_v = np.min(masked_data, axis=0, keepdims=True)


            self.metrics["normalized_feature_std"].value = bool(np.all(np.isclose(std_v, np.ones_like(std_v))) and \
                                                    np.all(np.isclose(mean_v, np.ones_like(mean_v))))

            self.metrics["normalized_feature_01"].value = bool(np.all(np.isclose(max_v, np.ones_like(max_v))) and \
                                                    np.all(np.isclose(min_v, np.zeros_like(min_v))))



