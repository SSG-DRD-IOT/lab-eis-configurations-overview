# Implementing an Classifier and Preprocessing Trigger based Intel® Edge Insights (EIS) Software

This lab shows the steps that an application developer will need to implement to create a video analytics solution on the Edge Insights Software framework.

## Reference Implementations on the Intel Development Zone

The Intel Developer Zones has many reference implementation applications, sample code snippets and whitepapers to help you start building with Intel technology.

On the [Industrial Reference Implementations and Code Samples](https://software.intel.com/en-us/industrial) page, you can browser difference ready-made applications. We will be reviewing the [Worker Safety Gear Detector Example](https://software.intel.com/en-us/iot/reference-implementations/safety-gear-detector) to the Edge Insights Software framework.

![](https://software.intel.com/sites/default/files/managed/66/c2/RefImpl-SafetyGear.jpg)


The video for the Worker Safety Gear Detector can be found on Github.
https://github.com/intel-iot-devkit/sample-videos

## Description of the Worker Safety Gear Detector that will be Ported to EIS

First let's look at the reference implementation of the Worker Safety Gear Detector. This is an OpenVino application which determines whether a worker is wearing their safety gear.
![](https://software.intel.com/sites/default/files/managed/2b/95/RefImpl-SafetyGear-graph-800.jpg)

## Steps to Port Application to EIS
First, let's review how the system is initialized and the steps that are needed in order to create a new application for EIS. 

 1. Create the new User Defined Function (UDF) that uses OpenVINO to detect safety vests and helmets. This is a Python file and a directory to hold related files such as the OpenVINO models and label files. Modify the runtime configuration file that are loaded into etcd at provisioning time.
 2. Modify the **etc_pre_load.json** to use the newly created UDF. 
 3. Build and Deploy application

### Prerequisites

First, be sure to review the documentation for User Defined Functions.
https://github.com/SSG-DRD-IOT/EIS-documentation/blob/master/udfs.md

### Setup Environmental Variables

For our convenience, let's set an environmental variable called **EIS_HOME** to refer to the root level directory of the Edge Insights Software.

**During the workshop be sure to check this location on YOUR COMPUTER or ask your instructor which directory EIS is installed in. **

```bash
export EIS_HOME=/home/eis/IEdgeInsights-worker-safety-gear
```

### Modify the Runtime Configuration 

All of the Runtime configurations for the docker containers in the EIS system are stored within etcd, a key value store that serves as a central repository for configuration.

Etcd reads in a configuration file located at 
**$EIS_HOME/docker_setup/provision/config/etd_pre_load.json**
 
The containers that are configured here include:
* VideoInvestion
* VideoAnalytics
* Visualizer
* InfluxDBConnector
* Kapacitor
* FactoryControlApp
* ImageStore

This file will contain a JSON object that defines the video sources, an UDF that implements a preprocessing filter location and a UDF the classifier function location.

We will set these configuration parameters in the restricted_zone_notifier.json application configuration file in the **video_file**, **model_xml**, **model_bin**, and **device** fields. 

For this example, we will send all frames in the video stream to the classifier. So we will use the **bypass_trigger** which sends all incoming frames to the classification engine. 

For the classification module we will point to the currently empty **restrictedzonenotifier** folder that we created earlier. 

Create the .json file:

### Video Ingestion Runtime Configuration

The **etd_pre_load.json** the video ingestion must be changed to use the **dummy** filter. This causes all video frames to be forwarded in the pipeline to the classification function.

```bash
gedit $EIS_HOME/docker_setup/provision/config/etd_pre_load.json
```

Next copy and paste this text into the newly created file:

```JSON
{
    "/VideoIngestion/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "ingestor": {
            "type": "opencv",
            "pipeline": "./test_videos/Safety_Full_Hat_and_Vest.mp4",
            "loop_video": "true",
            "queue_size": 10,
            "poll_interval": 0.2
        },
        "max_jobs": 20,
        "max_workers": 4,
        "udfs": [
            {
                "name": "dummy",
                "type": "native"
            }
        ]
    },
```

### Video Analytics Runtime Configuration

The **etd_pre_load.json** the video analytics must be changed to use the **dummy** filter. This causes all video frames to be forwarded in the pipeline to the classification function.

```bash
gedit $EIS_HOME/docker_setup/provision/config/etd_pre_load.json
```

```JSON   
"/VideoAnalytics/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "queue_size": 10,
        "max_jobs": 20,
        "max_workers": 4,
        "udfs": [
            {
                "name": "safety_gear.safety_classifier",
                "type": "python",
                "device": "CPU",
                "model_xml": "common/udfs/python/safety_gear/ref/frozen_inference_graph.xml",
                "model_bin": "common/udfs/python/safety_gear/ref/frozen_inference_graph.bin"
            }
        ]
    },
```

### The Entire etd_pre_load.json File

```JSON
{
    "/VideoIngestion/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "ingestor": {
            "type": "opencv",
            "pipeline": "./test_videos/Safety_Full_Hat_and_Vest.mp4",
            "loop_video": "true",
            "queue_size": 10,
            "poll_interval": 0.2
        },
        "max_jobs": 20,
        "max_workers": 4,
        "udfs": [
            {
                "name": "dummy",
                "type": "native"
            }
        ]
    },
    "/VideoAnalytics/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "queue_size": 10,
        "max_jobs": 20,
        "max_workers": 4,
        "udfs": [
            {
                "name": "safety_gear.safety_classifier",
                "type": "python",
                "device": "CPU",
                "model_xml": "common/udfs/python/safety_gear/ref/frozen_inference_graph.xml",
                "model_bin": "common/udfs/python/safety_gear/ref/frozen_inference_graph.bin"
            }
        ]
    },
    "/Visualizer/config": {
        "display": "true",
        "save_image": "false",
        "cert_path": ""
    },
    "/WebVisualizer/config": {
        "username": "admin",
        "password": "admin@123",
        "port": 5000
    },
    "/InfluxDBConnector/config": {
        "influxdb": {
            "retention": "1h30m5s",
            "username": "admin",
            "password": "admin123",
            "dbname": "datain",
            "ssl": "True",
            "verifySsl": "False",
            "port": "8086"
        },
        "pub_workers": "5",
        "sub_workers": "5"
    },
    "/Kapacitor/config": {
        "influxdb": {
            "username": "admin",
            "password": "admin123"
        }
    },
    "/FactoryControlApp/config": {
        "io_module_ip": "localhost",
        "io_module_port": 502,
        "red_bit_register": 20,
        "green_bit_register": 19
    },
    "/ImageStore/config": {
        "minio": {
            "accessKey": "admin",
            "secretKey": "password",
            "retentionTime": "1h",
            "retentionPollInterval": "60s",
            "ssl": "false"
        }
    },
    "/RestDataExport/config": {
        "camera1_stream_results": "http://localhost:8082",
        "camera1_stream": "http://localhost:8082",
        "http_server_ca": "/opt/intel/eis/cert.pem",
        "rest_export_server_host": "localhost",
        "rest_export_server_port": "8087"
    },
    "/GlobalEnv/": {
        "PY_LOG_LEVEL": "INFO",
        "GO_LOG_LEVEL": "INFO",
        "C_LOG_LEVEL": "INFO",
        "GO_VERBOSE": "0",
        "ETCD_KEEPER_PORT": "7070"
    },
    "/TLS_RemoteAgent/config": {
        "cert_path": "",
        "tls_host": "localhost",
        "user_labels": [
            {
                "VideoAnalytics": {
                    "0": "D_MISSING",
                    "1": "D_SHORT"
                }
            }
        ]
    }
}
```

### Creating the Classifier algorithm 

Intel Edge Insights Software provides for user defined functions to be created in either C++ or Python. 

If you'd like to review the C++ definition of the worker safety gear demo classifier it can be found at
**$EIS_HOME/common/udfs/native/safety_gear_demo/safety_gear_demo.cpp**


#### Python Analtyics Function

To define a Python function which uses OpenVINO to perform analytics on the frames in a video stream, you will need to define 3 functions.

**For this workshop the file has already been created for you. You do not need to copy and paste the code below**

`__init__` : The method used for initialization and loading the intermediate representation model into the plugin. 
 
`process` : The method used for inferencing and capturing the inference output.


### Import modules and create Classifier class

First we will import all python modules that will be used in the classifier algorithm and create the main **Classifier** class which will contain our methods:

First open our **safety_classifier.py** file:

```bash
gedit $EIS_HOME/common/udfs/python/safety_gear/safety_classifier.py
```

and import the following Python libraries:

```python

import os
import logging
import cv2
import numpy as np
import json
import threading
from openvino.inference_engine import IENetwork, IEPlugin
from distutils.util import strtobool
import time
import sys

```
### Create User Defined Function class

```python
class Udf:
    """Classifier object
    """
```

To create the `__init__` method we will check that the model files exist, load the plugin for CPU, load the CPU extension libraries, and check that the layers of the model are supported.

```python    
def __init__(self, model_xml, model_bin, device):
        """Constructor of Classifier class

        :param classifier_config: Configuration object for the classifier
        :type classifier_config: dict
        :param input_queue: input queue for classifier
        :type input_queue: queue
        :param output_queue: output queue of classifier
        :type output_queue: queue
        :return: Classification object
        :rtype: Object
        """
        self.log = logging.getLogger('WORKER_SAFETY_DETECTION')
        self.model_xml = model_xml
        self.model_bin = model_bin
        self.device = device

        assert os.path.exists(self.model_xml), \
            'Model xml file missing: {}'.format(self.model_xml)
        assert os.path.exists(self.model_bin), \
            'Model bin file missing: {}'.format(self.model_bin)

        # Load OpenVINO model
        self.irPlugin = IEPlugin(device=self.device.upper(), plugin_dirs="")
        if self.device == "CPU":
            cpu_ext = os.environ["INTEL_OPENVINO_DIR"]+'/inference_engine/lib/intel64/libcpu_extension_sse4.so'
            self.irPlugin.add_cpu_extension(cpu_ext)
        self.neuralNet = IENetwork.from_ir(
            model=self.model_xml, weights=self.model_bin)

        if self.irPlugin is not None and self.neuralNet is not None:
            self.inputBlob = next(iter(self.neuralNet.inputs))
            self.outputBlob = next(iter(self.neuralNet.outputs))
            self.neuralNet.batch_size = 1
            self.executionNet = self.irPlugin.load(network=self.neuralNet)

        self.profiling = bool(strtobool(os.environ['PROFILING_MODE']))


   ```

### Create Process method 

To create the `process` method we will use the section of the main function loop that runs the single shot detector on each frame as as well as the section of code that writes the alerts out to the screen as a basis.

This process method has 4 results that say which safety gear the worker is using a if they are safe or violating safety rules.

```JSON
{
	"1": "safety_helmet",
	"2": "safety_jacket",
	"3": "Safe",
	"4": "Violation"
}
```

Paste is the following code into our Classifier class:

```python
    # Main classification algorithm
    def process(self, frame, metadata):
        """Reads the image frame from input queue for classifier
        and classifies against the specified reference image.
        """
        if self.profiling is True:
            metadata['ts_va_classify_entry'] = time.time()*1000

        # Convert the buffer into np array.
        np_buffer = np.frombuffer(frame, dtype=np.uint8)
        if 'encoding_type' and 'encoding_level' in metadata:
            reshape_frame = np.reshape(np_buffer, (np_buffer.shape))
            reshape_frame = cv2.imdecode(reshape_frame, 1)
        else:
            reshape_frame = np.reshape(np_buffer, (int(metadata["height"]),
                                                    int(metadata["width"]),
                                                    int(metadata["channel"])
                                                    ))

        defects = []
        d_info = []

        n, c, h, w = self.neuralNet.inputs[self.inputBlob].shape
        cur_request_id = 0
        labels_map = None

        inf_start = time.time()
        initial_h = frame.shape[0]
        initial_w = frame.shape[1]

        in_frame = cv2.resize(frame, (w, h))
        # Change data layout from HWC to CHW
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape((n, c, h, w))
        self.executionNet.start_async(request_id=cur_request_id, inputs={
            self.inputBlob: in_frame})

        if self.executionNet.requests[cur_request_id].wait(-1) == 0:
            inf_end = time.time()
            det_time = inf_end - inf_start
            fps = str("%.2f" % (1/det_time))

            # Parse detection results of the current request
            res = self.executionNet.requests[cur_request_id].outputs[self.outputBlob]

            for obj in res[0][0]:
        	# obj[1] representing the category of the object detection
                # Draw only objects when probability more than specified threshold represented by obj[2]

                if obj[1] == 1 and obj[2] > 0.57: 
                    xmin = int(obj[3] * initial_w)
                    ymin = int(obj[4] * initial_h)
                    xmax = int(obj[5] * initial_w)
                    ymax = int(obj[6] * initial_h)
                    class_id = int(obj[1])
                    prob = obj[2]

		    #defect type returned as string, no user_labels mapping required
                    defects.append({'type': 'safety_helmet', 'tl':(xmin, ymin), 'br':(xmax, ymax)})


                if obj[1] == 2 and obj[2] > 0.525: 
                    xmin = int(obj[3] * initial_w)
                    ymin = int(obj[4] * initial_h)
                    xmax = int(obj[5] * initial_w)
                    ymax = int(obj[6] * initial_h)
                    class_id = int(obj[1])
                    prob = obj[2]

		    #defect type returned as string, no user_labels mapping required
                    defects.append({'type': 'safety_jacket', 'tl':(xmin, ymin), 'br':(xmax, ymax)})

                if obj[1] == 3 and obj[2] > 0.3:
                    xmin = int(obj[3] * initial_w)
                    ymin = int(obj[4] * initial_h)
                    xmax = int(obj[5] * initial_w)
                    ymax = int(obj[6] * initial_h)
                    class_id = int(obj[1])
                    prob = obj[2]

		    #defect type returned as string, no user_labels mapping required
                    defects.append({'type': 'safe', 'tl':(xmin, ymin), 'br':(xmax, ymax)})


                if obj[1] == 4 and obj[2] > 0.35:
                    xmin = int(obj[3] * initial_w)
                    ymin = int(obj[4] * initial_h)
                    xmax = int(obj[5] * initial_w)
                    ymax = int(obj[6] * initial_h)
                    class_id = int(obj[1])
                    prob = obj[2]

		    #defect type returned as string, no user_labels mapping required
                    defects.append({'type': 'violation', 'tl':(xmin, ymin), 'br':(xmax, ymax)})


        metadata["defects"] = defects

        if self.profiling is True:
            metadata['ts_va_classify_exit'] = time.time()*1000
        return False, None, metadata
 ```


### Messaging Thread

In the EIS framework, the messages are published over EIS Data Bus and can be subscribed to via OPC-UA by the OPC-UA Service. We will use an OPC-UA client to view those messages. This OPC/UA client is located in **$EIS_HOME/tools/visualizer** and does not need to be customized for this application.

You should now have a better idea of how an existing code base can be converted to Classifier and Trigger based Intel® Edge Insights (EIS) Software. In the next, lab we will implement all of these modules and run the restricted zone notifier using EIS.
