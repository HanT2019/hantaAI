import colorsys
import random

import numpy as np
from keras import backend as K
from keras.models import load_model
from PIL import Image

from yad2k.models.keras_yolo import yolo_eval, yolo_head

class Yolo:
    def __init__(self, model_path, anchors_path, classes_path):
        # for yad2k
        self.sess = None
        self.yolo_model = None
        self.class_names = None
        self.is_fixed_size = None
        self.model_image_size = None
        self.boxes, self.scores, self.classes = None, None, None
        self.input_image_shape = None

        self.results = {}

        self.sess = K.get_session()  # TODO: Remove dependence on Tensorflow session.

        with open(classes_path) as f:
            self.class_names = f.readlines()
        self.class_names = [c.strip() for c in self.class_names]

        with open(anchors_path) as f:
            anchors = f.readline()
            anchors = [float(x) for x in anchors.split(',')]
            anchors = np.array(anchors).reshape(-1, 2)

        self.yolo_model = load_model(model_path)

        # Verify model, anchors, and classes are compatible
        num_classes = len(self.class_names)
        num_anchors = len(anchors)
        # TODO: Assumes dim ordering is channel last
        model_output_channels = self.yolo_model.layers[-1].output_shape[-1]
        assert model_output_channels == num_anchors * (num_classes + 5), \
            'Mismatch between model and given anchor and class sizes. ' \
            'Specify matching anchors and classes with --anchors_path and ' \
            f'--classes_path flags.{model_output_channels}'

        # Check if model is fully convolutional, assuming channel last order.
        self.model_image_size = self.yolo_model.layers[0].input_shape[1:3]
        self.is_fixed_size = self.model_image_size != (None, None)

        # Generate colors for drawing bounding boxes.
        hsv_tuples = [(x / len(self.class_names), 1., 1.) for x in range(len(self.class_names))]
        self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self.colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), self.colors))
        random.seed(10101)  # Fixed seed for consistent colors across runs.
        random.shuffle(self.colors)  # Shuffle colors to decorrelate adjacent classes.
        random.seed(None)  # Reset seed to default.

        # Generate output tensor targets for filtered bounding boxes.
        # TODO: Wrap these backend operations with Keras layers.
        yolo_outputs = yolo_head(self.yolo_model.output, anchors, len(self.class_names))
        self.input_image_shape = K.placeholder(shape=(2, ))
        self.boxes, self.scores, self.classes = yolo_eval(
            yolo_outputs,
            self.input_image_shape,
            score_threshold=0.3,
            iou_threshold=0.5)

    def predict(self, image_path):
        if image_path in self.results.keys():
            return self.results[image_path]

        image = Image.open(image_path)
        if self.is_fixed_size:  # TODO: When resizing we can use minibatch input.
            resized_image = image.resize(
                tuple(reversed(self.model_image_size)), Image.BICUBIC)
            image_data = np.array(resized_image, dtype='float32')
        else:
            # Due to skip connection + max pooling in YOLO_v2, inputs must have
            # width and height as multiples of 32.
            new_image_size = (image.width - (image.width % 32),
                              image.height - (image.height % 32))
            resized_image = image.resize(new_image_size, Image.BICUBIC)
            image_data = np.array(resized_image, dtype='float32')

        image_data /= 255.
        image_data = np.expand_dims(image_data, 0)  # Add batch dimension.

        out_boxes, out_scores, out_classes = self.sess.run(
            [self.boxes, self.scores, self.classes],
            feed_dict={
                self.yolo_model.input: image_data,
                self.input_image_shape: [image.size[1], image.size[0]],
                K.learning_phase(): 0
            })

        return_values = []
        for i, c in reversed(list(enumerate(out_classes))):
            predicted_class = self.class_names[c]
            box = out_boxes[i]
            score = out_scores[i]

            label = '{} {:.2f}'.format(predicted_class, score)

            top, left, bottom, right = box
            top = max(0, np.floor(top + 0.5).astype('int32'))
            left = max(0, np.floor(left + 0.5).astype('int32'))
            bottom = min(image.size[1], np.floor(bottom + 0.5).astype('int32'))
            right = min(image.size[0], np.floor(right + 0.5).astype('int32'))

            return_values.append((predicted_class, top, left, bottom, right))

        self.results[image_path] = return_values

        # print(return_values)

        return return_values

    def get_colors(self, predicted_class):
        for c, class_name in enumerate(self.class_names):
            if predicted_class == class_name:
                return self.colors[c]
        return None
