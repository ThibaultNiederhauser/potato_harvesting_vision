import numpy as np
import cv2
import tensorflow as tf

from object_detection.utils import label_map_util
from scipy import ndimage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


# Patch the location of gfile
tf.gfile = tf.io.gfile



class ObjectDetection():

    def __init__(self, path_to_frozen_graph, path_to_label_map, num_classes, seg_type, threshold):

        #object detection NN parameter
        self.path_to_frozen_graph = path_to_frozen_graph
        self.path_to_label_map = path_to_label_map
        self.num_classes = num_classes
        self.threshold = threshold


        #get model
        self.read_model()

        #detection variables

        #list of detected objects above threshold
        self.boxes_s   = None
        self.classes_s = None
        self.scores_s  = None



    def read_model(self):
        print("reads frozen graph")
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.gfile.GFile(self.path_to_frozen_graph, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        print("reads label map")
        label_map = label_map_util.load_labelmap(self.path_to_label_map)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self.num_classes,
                                                                    use_display_name=True)
        category_index = label_map_util.create_category_index(categories)

        return category_index, detection_graph

    def object_detection(self, detection_graph, sess, image_np):
        # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image_np, axis=0)
        # Extract image tensor
        image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
        # Extract detection boxes
        boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
        # Extract detection scores
        scores = detection_graph.get_tensor_by_name('detection_scores:0')
        # Extract detection classes
        classes = detection_graph.get_tensor_by_name('detection_classes:0')
        # Extract number of detections
        num_detections = detection_graph.get_tensor_by_name(
            'num_detections:0')
        # Actual detection.
        (boxes, scores, classes, num_detections) = sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})

        boxes = np.squeeze(boxes)
        classes = np.squeeze(classes)
        scores = np.squeeze(scores)

        boxes_s, classes_s, scores_s = self.select_objects(boxes, classes, scores, self.threshold)

        return boxes_s, classes_s, scores_s

    def select_objects(self, boxes, classes, scores, thres):
        idx = np.where(scores >= thres)[0]
        if idx.size > 0:
            boxes = boxes[idx, :]
            classes = classes[idx]
            scores = scores[idx]

        else:
            boxes = []
            classes = []
            scores = []

        return np.array(boxes), np.array(classes), np.array(scores)



