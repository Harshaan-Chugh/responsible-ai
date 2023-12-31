# Copyright 2022 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


import json
import subprocess
import threading
import redis
import RAI
import os
import numpy as np 
from json import JSONEncoder
import logging
from RAI.Analysis import AnalysisManager
import time

logger = logging.getLogger(__name__)


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


__all__ = ['RaiRedis']


class RaiRedis:
    """
    RaiRedis is used to provide Redis functionality. Allows for adding measurements, deleting measurements,
    exporting metadata. Standard port: 6379, db=0.
    """

    def __init__(self, ai_system: RAI.AISystem = None) -> None:
        self.redis_connection = None
        self.ai_system = ai_system
        self._ai_request_pub = None
        self._threads = []
        self.analysis_manager = AnalysisManager()

    def connect(self, host: str = "localhost", port: int = 6379) -> bool:
        self.redis_connection = redis.Redis(host=host, port=port, db=0)
        self._init_analysis_pubsub()
        return self.redis_connection.ping()

    def get_progress_update_lambda(self, analysis):
        return lambda progress: self.analysis_progress_update(analysis, progress)

    def analysis_progress_update(self, analysis: str, progress):
        self.redis_connection.publish("ai_requests", self.ai_system.name + '|start_analysis_update|' +
                                      analysis + "|" + progress)

    def _init_analysis_pubsub(self):
        def sub_handler(msg):
            logger.info(f"New Analysis message received: {msg}")
            msg = msg['data'].decode("utf-8").split('|')
            if msg[0] == self.ai_system.name:
                if msg[1] == "available_analysis":  # Request for the available analysis
                    available = self.analysis_manager.get_available_analysis(self.ai_system, msg[2])
                    self.redis_connection.publish("ai_requests", self.ai_system.name+'|available_analysis_response|'+json.dumps(available))
                elif msg[1] == "start_analysis":  # Request to start a specific analysis
                    dataset = msg[2]
                    analysis = msg[3]
                    if analysis in self.analysis_manager.get_available_analysis(self.ai_system, msg[2]):
                        connection = self.get_progress_update_lambda(analysis)
                        x = threading.Thread(target=self._run_analysis_thread, args=(dataset, analysis, connection))
                        x.start()

        self._ai_request_pub = self.redis_connection.pubsub()
        try:
            logger.info("channel subscribed")
            self._ai_request_pub.subscribe(**{"ai_requests": sub_handler})
            self._threads.append(self._ai_request_pub.run_in_thread(sleep_time=.1))
        except:
            logger.warning("unable to subscribe to redis pub/sub")

    # def __del__(self):
    #     print("inside del")
    #     self.Disconnect()
    #     print("inside del: after disconnect")
        
    def Disconnect(self):
        
        self._ai_request_pub.unsubscribe("ai_requests")
        for thread in self._threads:
            thread.stop()
            
        
        time.sleep(.5)
        self._ai_request_pub.close()
        self.redis_connection.connection_pool.disconnect()

    def _run_analysis_thread(self, dataset, analysis, connection):
        result = self.analysis_manager.run_analysis(self.ai_system, dataset, analysis, connection=connection)
        # encoded_res = pickle.dumps(result[analysis].to_html())
        encoded_res = json.dumps(self._jsonify_analysis(result[analysis].to_html()))
        self.redis_connection.set(self.ai_system.name + "|analysis|"+analysis, encoded_res)
        self.redis_connection.publish("ai_requests", self.ai_system.name + '|start_analysis_response|' +
                                      analysis + "|COMPLETE")

    def _jsonify_analysis(self, analysis):
        if "dash" in str(type(analysis)) or "plotly" in str(type(analysis)):
            analysis = analysis.to_plotly_json()
        if isinstance(analysis, dict):
            for key in analysis:
                analysis[key] = self._jsonify_analysis(analysis[key])
        elif isinstance(analysis, list):
            for i in range(len(analysis)):
                analysis[i] = self._jsonify_analysis(analysis[i])
        elif isinstance(analysis, np.ndarray):
            analysis = analysis.tolist()
        return analysis

    def reset_redis(self, export_metadata: bool = True) -> None:
        to_delete = ["metric_values", "model_info", "metric_info", "metric", "certificate_metadata",
                     "certificate_values", "certificate"]
        for key in to_delete:
            self.redis_connection.delete(self.ai_system.name + "|" + key)
        for key in self.redis_connection.scan_iter(self.ai_system.name + "|analysis|*"):
            self.redis_connection.delete(key)
        if export_metadata:
            self.export_metadata()
        self.redis_connection.publish('update', "cleared")

    def delete_data(self, system_name) -> None:
        to_delete = ["metric_values", "model_info", "metric_info", "metric", "certificate_metadata",
                     "certificate_values", "certificate", "certificate_info", "project_info"]
        for key in to_delete:
            self.redis_connection.delete(system_name + "|" + key)
        for key in self.redis_connection.scan_iter(self.ai_system.name + "|analysis|*"):
            self.redis_connection.delete(key)
        self.redis_connection.srem("projects", system_name)
        self.redis_connection.publish('update', "cleared")

    def delete_all_data(self):
        print("Deleting!")
        for key in self.redis_connection.scan_iter("*|project_info"):
            val = key[:-13].decode("utf-8")
            print("Deleting: ", val)
            self.delete_data(val)

    def export_metadata(self) -> None:
        metric_info = self.ai_system.get_metric_info()
        certificate_info = self.ai_system.get_certificate_info()
        project_info = self.ai_system.get_project_info()

        self.redis_connection.set(self.ai_system.name + '|metric_info', json.dumps(metric_info))
        self.redis_connection.set(self.ai_system.name + '|certificate_info', json.dumps(certificate_info))
        self.redis_connection.set(self.ai_system.name + '|project_info', json.dumps(project_info))
        self.redis_connection.sadd("projects", self.ai_system.name)

    def export_visualizations(self, model_interpretation_dataset: str, data_visualization_dataset: str):
        data_visualizations = ["DataVisualization"]
        interpretations = ["GradCamAnalysis"]
        for analysis in data_visualizations:
            if data_visualization_dataset:
                connection = self.get_progress_update_lambda(analysis)
                result = self.analysis_manager.run_analysis(self.ai_system, data_visualization_dataset, analysis, connection)
                encoded_res = json.dumps(self._jsonify_analysis(result[analysis].to_html()))
                self.redis_connection.set(self.ai_system.name + "|analysis|" + analysis, encoded_res)
        for analysis in interpretations:
            if model_interpretation_dataset:
                connection = self.get_progress_update_lambda(analysis)
                result = self.analysis_manager.run_analysis(self.ai_system, model_interpretation_dataset, analysis, connection)
                if analysis in result:
                    encoded_res = json.dumps(self._jsonify_analysis(result[analysis].to_html()))
                    self.redis_connection.set(self.ai_system.name + "|analysis|" + analysis, encoded_res)

    def add_measurement(self) -> None:
        certificates = self.ai_system.get_certificate_values()
        metrics = self.ai_system.get_metric_values()
        print("Sharing: ", self.ai_system.name)
        self.redis_connection.rpush(self.ai_system.name + '|certificate_values', json.dumps(certificates))  # True
        # Leaving this for now.
        # TODO: Set up standardized to json for all metrics.
        '''
        # print("METRICS: ", metrics)
        for dataset in metrics:
            for group in metrics[dataset]:
                for m in metrics[dataset][group]:
                    print(m, "\n")
                    
        print("testing json dumps: \n")
        for dataset in metrics:
            for group in metrics[dataset]:
                for m in metrics[dataset][group]:
                    if "moment" in m:
                        continue
                    print(m, "\n")
                    print(metrics[dataset][group][m])
                    print(json.dumps(metrics[dataset][group][m]))
        '''

        self.redis_connection.rpush(self.ai_system.name + '|metric_values', json.dumps(metrics))  # True
        self.redis_connection.publish('update',
                                      "New measurement: %s" % metrics[list(metrics.keys())[0]]["metadata"]["date"])

    def viewGUI(self):
        gui_launcher = threading.Thread(target=self._view_gui_thread, args=[])
        gui_launcher.start()

    def _view_gui_thread(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        os.chdir("../../Dashboard")
        file = os.path.abspath("main.py")
        subprocess.call("start /wait python " + file, shell=True)
        print("GUI can be viewed in new terminal")
