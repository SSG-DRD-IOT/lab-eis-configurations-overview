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
 13 # Docker security
 14 EIS_USER_NAME=eisuser
 15 EIS_UID=5319

 17 # This is the path where EIS package is installed
 18 EIS_INSTALL_PATH=/opt/intel/eis

 25 # DEV_MODE if set `true` allows one to run EIS in non-secure mode and provides additional UX/DX etc.,
 26 DEV_MODE=false
 27 # PROFILING_MODE is set 'true' allows to generate profile/performance data
 28 PROFILING_MODE=false

 45 # Etcd settings
 46 ETCD_NAME=master
 47 ETCD_VERSION=v3.4.0
 48 ETCD_DATA_DIR=/EIS/etcd/data/
 49 ETCD_RESET=true
 50 ETCD_CLIENT_PORT=2379
 51 ETCD_PEER_PORT=2380
 52 # For proxy environment, please append IP addresses or Range IP addresses of each node of the cluster to no_proxy
 53 # e.q. no_proxy=localhost,127.0.0.1,10.223.109.130,10.223.109.170
 54 no_proxy=localhost,127.0.0.1
 55 
 56 # TLS ciphers for ETCD, INFLUXDB
 57 TLS_CIPHERS=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
 58 SSL_KEY_LENGTH=3072
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
  2     "/VideoIngestion/config": {
  3         "ingestor": {
  4             "video_src": "./test_videos/pcb_d2000.avi",
  5             "encoding": {
  6                 "type": "jpg",
  7                 "level": 100
  8             },
  9             "loop_video": "true",
 10             "poll_interval": 0.2
 11         },
 12         "filter": {
 13             "name": "pcb_filter",
 14             "queue_size": 10,
 15             "max_workers": 1,
 16             "training_mode": "false",
 17             "n_total_px": 300000,
 18             "n_left_px": 1000,
 19             "n_right_px": 1000
 20         }
 21 
 22     },
```

Here is an example of two cameras. The first camera uses RTSP and the second camera uses serial communications. both have a bypass filter defined.
```json
2     "/VideoIngestion1/config": {
  3         "ingestor": {
  4         "video_src": "rtspsrc location=\"rtsp://localhost:8554/\" latency=100 ! rtph264depay ! h264parse ! vaapih264dec ! vaapipostproc format=bgrx ! videoconvert ! appsink max_buffers=2 drop=TRUE",
  5         "encoding": {
  6             "type": "jpg",
  7             "level": 100
  8         },
  9         "poll_interval": 0.2
 10     },
 11     "filter": {
 12         "name": "bypass_filter",
 13         "queue_size": 10,
 14         "max_workers": 1,
 15         "training_mode": "false"
 16     }
 17 
 18     },
 19     "/VideoIngestion2/config": {
 20         "ingestor": {
 21             "video_src": "pylonsrc serial=22573662 imageformat=yuv422 exposureGigE=3250 interpacketdelay=1500 ! videoconvert ! appsink",
 22             "encoding": {
 23                 "type": "jpg",
 24                 "level": 100
 25             },
 26             "poll_interval": 0.2
 27         },
 28         "filter": {
 29             "name": "bypass_filter",
 30             "queue_size": 10,
 31             "max_workers": 1,
 32             "training_mode": "false",
 33             "n_total_px": 300000,
 34             "n_left_px": 1000,
 35             "n_right_px": 1000
 36         }
 37 
 38     },
```

Notice that the filters are defined along with any arguments that need to be passed to the filter.


### Video Classification Setup
The **$EIS_HOME/docker_setup/provision/config/etcd_pre_load.json** file also sets up the classification step of the pipeline. 
**pcb_classifier** is a python file defined by the video analytics developer. It will use OpenVINO to run the neural network defined by **model_xml** and **model_bin**

 23     "/VideoAnalytics/config": {
 24         "name": "pcb_classifier",
 25         "queue_size": 10,
 26         "max_workers": 1,
 27         "ref_img": "./VideoAnalytics/classifiers/ref_pcbdemo/ref.png",
 28         "ref_config_roi": "./VideoAnalytics/classifiers/ref_pcbdemo/roi_2.json",
 29         "model_xml": "./VideoAnalytics/classifiers/ref_pcbdemo/model_2.xml",
 30         "model_bin": "./VideoAnalytics/classifiers/ref_pcbdemo/model_2.bin",
 31         "device": "CPU"
 32     },


:warning: This folder must be in this location and have the same name as the classifier to function. 

The **config** section defines all of the arguments that are passed to the classifier. This particular classifier will use OpenVINO :wine_glass:. OpenVINO requires a **neural network model file** in itermediate representation format and the **device hardware** that the inference will be run on.


### Frame/Image Storage and Alerts and Notifications

InfluxDB is used to store the meta data that the Classifier generates. This information is the result of the OpenVINO classication.

Kapacitor is the alerting system that can be configured to run scripts or send notifications when an Image is classified.

```json
 38     "/InfluxDBConnector/config": {
 39         "influxdb": {
 40             "retention": "1h30m5s",
 41             "username": "admin",
 42             "password": "admin123",
 43             "dbname": "datain",
 44             "ssl": "True",
 45             "verifySsl": "False",
 46             "port": "8086"
 47         },
 48         "pub_workers" : "5",
 49         "sub_workers" : "5"
 50     },
 51     "/Kapacitor/config": {
 52         "influxdb": {
 53             "username": "admin",
 54             "password": "admin123"
 55         }
 56     },
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
Once the application successfully runs. The output window will be poped up as below.
![](images/pcbdemo_result.png)


You should now understand the Intel® Edge Insights Software framework components and how run pcbdemo application successfully.    
Let's Deploy a Restricted Zone Notifier Reference implementation using Intel® Edge Insights Software framework in our next lab.

## Next Lab
[Understanding of Converting Python based RI to classifier and trigger based IEI Software](./understanding_ri_to_eis_conversion.md)
