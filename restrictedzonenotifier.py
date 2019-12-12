# Copyright (c) 2019 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import logging
import cv2
import numpy as np
import json
import threading

from .defect import Defect
from libs.base_classifier import BaseClassifier
from openvino.inference_engine import IENetwork, IEPlugin
from distutils.util import strtobool
import time

import sys

# minMatches = 10
# D_MISSING = 0
# D_SHORT = 1
# PERSON_DETECTED = 1
from collections import namedtuple

MyStruct = namedtuple("assemblyinfo", "safe")
INFO = MyStruct(True)
PERSON_DETECTED = 1


def trace_calls(frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    func_line_no = frame.f_lineno
    func_filename = co.co_filename
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    logging.info('Call to %s on line %s of %s from line %s of %s' % \
                 (func_name, func_line_no, func_filename,
                  caller_line_no, caller_filename))
    return


# sys.settrace(trace_calls)

class Classifier(BaseClassifier):
    """Classifier object
    """

    def __init__(self, classifier_config, input_queue, output_queue):
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
        logging.info('Launching restrictedzonenotififier.py __init__ method')
        super().__init__(classifier_config, input_queue, output_queue)
        # self.log = logging.getLogger('PCB_DEFECT_DETECTION')
        self.model_xml = classifier_config["model_xml"]
        self.model_bin = classifier_config["model_bin"]
        self.device = classifier_config["device"]

        # Assert all input parameters exist
        assert os.path.exists(self.model_xml), \
            'Tensorflow model missing: {}'.format(self.model_xml)
        assert os.path.exists(self.model_bin), \
            'Tensorflow model bin file missing: {}'.format(self.model_bin)

        # Load OpenVINO model
        self.plugin = IEPlugin(device=self.device.upper(), plugin_dirs="")
        self.net = IENetwork.from_ir(model=self.model_xml,
                                     weights=self.model_bin)
        self.input_blob = next(iter(self.net.inputs))
        self.output_blob = next(iter(self.net.outputs))
        self.net.batch_size = 1  # change to enable batch loading
        self.exec_net = self.plugin.load(network=self.net)
        self.profiling = bool(strtobool(os.environ['PROFILING_MODE']))

    def ssd_out(self, res, initial_wh, selected_region):
        """
        Parse SSD output.

        :param res: Detection results
        :param args: Parsed arguments
        :param initial_wh: Initial width and height of the frame
        :param selected_region: Selected region coordinates
        :return: safe,person
        """
        logging.info("called ssd_out with res, initial_wh, selected_region:")
        #logging.info(res)
        #logging.info(initial_wh)
        #logging.info(selected_region)
        global INFO
        person = []
        INFO = INFO._replace(safe=True)

        for obj in res[0][0]:
            # Draw objects only when probability is more than specified threshold
            if obj[2] > 0.5:
                xmin = int(obj[3] * initial_wh[0])
                ymin = int(obj[4] * initial_wh[1])
                xmax = int(obj[5] * initial_wh[0])
                ymax = int(obj[6] * initial_wh[1])
                person.append([xmin, ymin, xmax, ymax])

        for p in person:
            # area_of_person gives area of the detected person
            area_of_person = (p[2] - p[0]) * (p[3] - p[1])
            x_max = max(p[0], selected_region[0])
            x_min = min(p[2], selected_region[0] + selected_region[2])
            y_min = min(p[3], selected_region[1] + selected_region[3])
            y_max = max(p[1], selected_region[1])
            point_x = x_min - x_max
            point_y = y_min - y_max
            # area_of_intersection gives area of intersection of the
            # detected person and the selected area
            area_of_intersection = point_x * point_y
            if point_x < 0 or point_y < 0:
                continue
            else:
                if area_of_person > area_of_intersection:
                    # assembly line area flags
                    INFO = INFO._replace(safe=True)
                else:
                    # assembly line area flags
                    INFO = INFO._replace(safe=False)
        return INFO.safe, person

    # Main classification algorithm
    def classify(self):
        """Reads the image frame from input queue for classifier
        and classifies against the specified reference image.
        """
        logging.info('Launching restrictedzonenotififier.py classify method')
        logging.info('stop_ev_is_set=%s', self.stop_ev.is_set())
        frame_count = 0
        while not self.stop_ev.is_set():
            metadata, frame = self.input_queue.get()
            logging.info('metadata=%s', metadata)
            logging.info('frame type=%s', type(frame))
            p_detect = []
            frame_count = frame_count + 1

            # if self.profiling is True:
            #    metadata['ts_va_classify_entry'] = time.time() * 1000

            # logging.info("profiling true, metadata=%s ", metadata['ts_va_classify_entry'])

            # Convert the buffer into np array.
            # logging.info("frame=%s", frame)
            np_buffer = np.frombuffer(frame, dtype=np.uint8)
            if 'encoding_type' and 'encoding_level' in metadata:
                reshape_frame = np.reshape(np_buffer, (np_buffer.shape))
                reshape_frame = cv2.imdecode(reshape_frame, 1)
            else:
                reshape_frame = np.reshape(np_buffer, (int(metadata["height"]),
                                                       int(metadata["width"]),
                                                       int(metadata["channel"])
                                                       ))

            initial_wh = [reshape_frame.shape[1], reshape_frame.shape[0]]
            n, c, h, w = self.net.inputs[self.input_blob].shape
            roi_x, roi_y, roi_w, roi_h = [0, 0, 0, 0]

            if roi_x <= 0 or roi_y <= 0:
                roi_x = 0
                roi_y = 0
            if roi_w <= 0:
                roi_w = reshape_frame.shape[1]
            if roi_h <= 0:
                roi_h = reshape_frame.shape[0]
            cv2.rectangle(reshape_frame, (roi_x, roi_y),
                          (roi_x + roi_w, roi_y + roi_h), (0, 0, 255), 2)
            selected_region = [roi_x, roi_y, roi_w, roi_h]
            in_frame_fd = cv2.resize(reshape_frame, (w, h))
            # Change data layout from HWC to CHW
            in_frame_fd = in_frame_fd.transpose((2, 0, 1))
            in_frame_fd = in_frame_fd.reshape((n, c, h, w))

            # Start asynchronous inference for specified request.
            logging.info("starting inference")
            inf_start = time.time()

            res = self.exec_net.infer(inputs={self.input_blob: in_frame_fd})

            # self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame_fd})
            # self.infer_status = self.exec_net.requests[0].wait()
            det_time = time.time() - inf_start
            res = res[self.output_blob]
            # res = self.exec_net.requests[0].outputs[self.output_blob]
#            logging.info("result=%s ", res)
            # Parse SSD output
 #           logging.info(selected_region)
  #          logging.info(self.ssd_out)
            logging.info("Process output #{}".format(frame_count))
            safe, person = self.ssd_out(res, initial_wh, selected_region)

            logging.info(safe)
            logging.info(person)
            if person:
                x, y, x1, y1 = [person[0][i] for i in (0, 1, 2, 3)]
                p_detect.append(Defect(PERSON_DETECTED, (x, y), (x1, y1)))

            # Draw performance stats
            # inf_time_message = "Inference time: {:.3f} ms".format(det_time * 1000)
            # throughput = "Throughput: {:.3f} fps".format(1000 * frame_count / (det_time * 1000))

            # d_info.append(DisplayInfo(inf_time_message, 0))
            # d_info.append(DisplayInfo(throughput, 0))
            # if not safe display HIGH [priority: 2] alert string
            '''
            if p_detect:
                warning = "HUMAN IN ASSEMBLY AREA: PAUSE THE MACHINE!"
                d_info.append(DisplayInfo('Worker Safe: False', 2))
                d_info.append(DisplayInfo(warning, 2))
            else:
                d_info.append(DisplayInfo('Worker Safe: True', 0))

            logging.info("d_info:")
            logging.info(d_info)
            '''
            defects=[]
            for d in p_detect:
                if d.defect_class == PERSON_DETECTED:
                    defects.append({
                        'type': d.defect_class,
                        'tl': d.tl,
                        'br': d.br
                    })
                else:
                    logging.info("None")

            metadata["display_info"] = defects

            if self.profiling is True:
                metadata['ts_va_classify_exit'] = time.time() * 1000

            logging.info('SENDING FRAME {} TO OUTPUT QUEUE'.format(frame_count))
            #logging.info('metadata:%s ', metadata)
            self.output_queue.put((metadata, frame))
            logging.info('Frame sent to queue')
            self.log.info("metadata: {} added to output queue".format(
                metadata))
