# Explore Intel® Edge Insights Software
## What is Intel® Edge Insights Software
Industrial Edge Insights Software (EIS) from Intel is a reference implementation of an analytics pipeline. The pipeline is designed as a set of micro-services that the customer can deploy in different configurations.

Edge Insights Software (EIS) implements the data ingestion, storage, alerting and monitoring and all the infrustructure software to support analytics applications. This leaves you, as the developer or systems integrator to focus on creating the application and not the infrastructure.  

In this lab, we will walk through the key files that the application developer will need to configure the build process and the microservices runtime.

## Configuration Overview

### The EtcD Key-Value Service Holds a Deployments Configuration

To learn more about etcd visit its homepage on Github at https://github.com/etcd-io/etcd

## Build Configurations

**$EIS_HOME/docker_setup/.env** contains all of the environmental variables for the micro-service build process. This includes Shell variables and Docker environmental variables.

Here are some of the important lines in the build configuration file
```sh
 # Docker security
 EIS_USER_NAME=eisuser
 EIS_UID=5319

 # This is the path where EIS package is installed
 EIS_INSTALL_PATH=/opt/intel/eis

 # DEV_MODE if set `true` allows one to run EIS in non-secure mode and provides additional UX/DX etc.,
 DEV_MODE=false
 # PROFILING_MODE is set 'true' allows to generate profile/performance data
 PROFILING_MODE=false

 # Etcd settings
 ETCD_NAME=master
 ETCD_VERSION=v3.4.0
 ETCD_DATA_DIR=/EIS/etcd/data/
 ETCD_RESET=true
 ETCD_CLIENT_PORT=2379
 ETCD_PEER_PORT=2380
 # For proxy environment, please append IP addresses or Range IP addresses of each node of the cluster to no_proxy
 # e.q. no_proxy=localhost,127.0.0.1,10.223.109.130,10.223.109.170
 no_proxy=localhost,127.0.0.1
 
 # TLS ciphers for ETCD, INFLUXDB
TLS_CIPHERS=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA3
 SSL_KEY_LENGTH=3072
```

## Runtime Configurations

When the microservices start EtcD will come online. EtcD stores all of runtime configurations of the EIS system in a distributed and fault tolerant manner.

### The etcd_pre_load.json File
The **$EIS_HOME/docker_setup/provision/config/etcd_pre_load.json** file contains all of the default values that the system uses to initialize itself.

Each stage of the Video Analytics Pipeline has a configuration section.


### Video Ingestion

Video Ingestion is a service that defines the video sources. The sources can either be from a file stream or from a camera and more than 1 video ingestor can be defined. 

### Filters
The video ingestor also supports a filter than will be call on each frame. The filter can be used to set up filter criteria that allows the video analytics developer remove video frames from the pipeline before they are sent to the OpenVINO neural network step in the pipeline. This allows the video analytics developer to setup up a quick executing algorithm to elimentate frames before they are sent to the more computationally intensive computer visions steps of the pipeline.

This filters the incoming data stream, mainly to reduce the storage and computation requirements by only passing frames of interest. All input frames are passed to the Filter. 

![](images/VideoIngestion.png)

Here is an example of configuring a video file source.
```json
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

Here is an example of two cameras. The first camera uses RTSP and the second camera uses serial communications. both have a bypass filter defined.
```json
    "/VideoIngestion1/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "ingestor": {
            "type": "opencv",
            "pipeline": "./test_videos/pcb_d2000.avi",
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
    "/VideoIngestion2/config": {
        "encoding": {
            "type": "jpeg",
            "level": 95
        },
        "ingestor": {
            "type": "opencv",
            "pipeline": "pylonsrc serial=22573662 imageformat=yuv422 exposureGigE=3250 interpacketdelay=6000 ! videoconvert ! appsink"
        }
    },
```

Notice that the filters are defined along with any arguments that need to be passed to the filter.


### Video Classification Setup
The **$EIS_HOME/docker_setup/provision/config/etcd_pre_load.json** file also sets up the classification step of the pipeline. 
**pcb_classifier** is a python file defined by the video analytics developer. It will use OpenVINO to run the neural network defined by **model_xml** and **model_bin**


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


:warning: This folder must be in this location and have the same name as the classifier to function. 

The **config** section defines all of the arguments that are passed to the classifier. This particular classifier will use OpenVINO :wine_glass:. OpenVINO requires a **neural network model file** in itermediate representation format and the **device hardware** that the inference will be run on.


### Frame/Image Storage and Alerts and Notifications

InfluxDB is used to store the meta data that the Classifier generates. This information is the result of the OpenVINO classication.

Kapacitor is the alerting system that can be configured to run scripts or send notifications when an Image is classified.

```json
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
          "pub_workers" : "5",
          "sub_workers" : "5"
      },
      "/Kapacitor/config": {
          "influxdb": {
              "username": "admin",
              "password": "admin123"
          }
      },
```

##### Visualizer
      The visualizer is not a video viewer! It is pulling frames that have a classification result from the object store and displaying them rapidly one after another.

*Location:*~/Workshop/IEdgeInsights-v1.5LTS/tools/visualizer/


### Data Flow in Edge Insights Software

We have reviewed the architectural components of EIS. Now let's understand how data flows between these components.

![](images/eis-overview.png)

**Step-1.a:**
The Video Ingestion module starts capturing frames from Basler camera /
RTSP camera (or video file) and sends the frames to the Trigger Algorithm.

**Step-1.b:**
The Trigger Algorithm will determine the relevant frames that are to go to
the Classifier. In the PCB demo use case, the Trigger Algorithm selects the images with the full PCB within view and send relavant frames to teh Video Ingestion.

**Step-2:**
The relevant frames from the Trigger Algorithm are stored into Image Store and the corresponding meta-data is stored in InfluxDB

**Step-3:**
Kapacitor subscribes to the Meta Data stream. All the streams in InfluxDB are subscribed as default by Kapacitor.

**Step-4:**
The Classifier UDF (User Defined Function) receives the Meta Data from Kapacitor. It then invokes the UDF classifier algorithm.

**Step-5:**
UDF Classifier Algorithm fetches the image frame from the Image Store and
generates the Classified Results with defect information, if any. Each frame
produces one set of Classified Results.

**Step-6:**
The Classifier UDF returns the classified results to Kapacitor.

**Step-7:**
The Kapacitor saves the Classified Results to InfluxDB. This behavior is enforced in the Kapacitor TICK script.

**Step-8:**
The Classified Results are received by Factory Control Application.

**Step-9:**
The Factory Control Application will turn on the alarm light if a defect is found in the part.

**Step-10:**
The Stream Manager subscribes to the Classified Results stream. The policy of stream export is set in the Stream Manager.

**Step-11:**
The Stream Manager uses the Data Bus Abstraction module interfaces to publish the Classified Results stream. The Data Bus Abstraction provides a publish-subscribe interface.

**Step-12:**
Data Bus Abstraction creates an OPC-UA Server, which exposes the Classified Results data as a string.

**Step-13:**
The Classified result is published in the OPC-UA message bus and available to external applications

**Step-14:**
The image handle of the actual frame is part of the Classified Results. The raw image can be retrieved through the data agent using the GetBlob() API.

**Step-15:**
The raw image frame is returned in response to the GetBlob() command.


**NOTE:** As an application developer, you do not need to worry about handling the data flow described above from data ingestion to classification. The included software stack using InfluxDB and Kapacitor handle the data movement and storage.


### Running Defect detection demo application                            
**Description**   
Printed Circuits Boards(PCBs) are being inspected for quality control to check if any defects(missing component or components are short) are there with the PCBs. To find out the defects a good quality PCB will be compared against the defective ones and pin point the location of the defect as well.

Input to the application can be from a live stream or from a video file. Here video file (~/$EIS_HOME/docker_setup/test_videos/pcb_d2000.avi) is used for this demo.

**Build and Run Sample.**  
To **build and run** the sample pcbdemo sample application execute the following commands.

```bash
cd ~/$EIS_HOME/docker_setup/

cd provision
./provision_eis.sh ../docker-compose.yml

cd ..
sudo su
docker-compose up --build -d
```

Once this completes run the following command to view the log:

```bash
tail -f /opt/intel/iei/logs/consolidatedLogs/iei.log
```
If everything is running properly you will see:

```
ia_data_agent         | I0829 11:46:55.835922       6 StreamManager.go:191] Publishing topic: stream1_results
```
Which is indicating that the ia_data_agent container is streaming data on the "stream1_results" topic. 

To **Visualize** the sample application , execute the below command:

```bash
cd ~/$EIS_HOME/tools/visualizer
source ./source.sh
python3 visualize.py -D true
```
This will run the vizualizer in developer mode (no certificates needed). 

**Pcb-Demo Output**   

You should now understand the Intel® Edge Insights Software framework components and how run pcbdemo application successfully.    
Let's Deploy a Restricted Zone Notifier Reference implementation using Intel® Edge Insights Software framework in our next lab.

## Next Lab
[Understanding of Converting Python based RI to classifier and trigger based IEI Software](./understanding_ri_to_eis_conversion.md)
