#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.

import logging

from caffe2.python import core
from caffe2.python.onnx.workspace import Workspace
from caffe2.python.predictor.predictor_exporter import (
    prepare_prediction_net,
    save_to_db,
)
from ml.rl.training.rl_predictor_pytorch import RLPredictor


logger = logging.getLogger(__name__)


class _ParametricDQNPredictor(RLPredictor):
    def __init__(self, pem, ws, predict_net=None):
        super(_ParametricDQNPredictor, self).__init__(
            net=None, init_net=None, parameters=None, int_features=None, ws=ws
        )
        self.pem = pem
        self._predict_net = predict_net

    @property
    def predict_net(self):
        if self._predict_net is None:
            self._predict_net = core.Net(self.pem.predict_net)
            self.ws.CreateNet(self._predict_net)
        return self._predict_net

    def predict(self, float_state_features, int_state_features, actions):
        assert not int_state_features, "Not implemented"

        float_examples = []
        for i in range(len(float_state_features)):
            float_examples.append({**float_state_features[i], **actions[i]})

        return super(_ParametricDQNPredictor, self).predict(float_examples)

    def save(self, db_path, db_type):
        # The workspace here is expected to be the Workspace class from ONNX
        with self.ws._ctx:
            save_to_db(db_type, db_path, self.pem)

    @classmethod
    def load(cls, db_path, db_type, *args, **kwargs):
        ws = Workspace()
        with ws._ctx:
            net = prepare_prediction_net(db_path, db_type)
            # TODO: reconstruct pem if so the predictor can be saved back
        return cls(pem=None, ws=ws, predict_net=net)
