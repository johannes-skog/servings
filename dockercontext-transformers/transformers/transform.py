import kserve
from typing import List, Dict, Union
import logging
import numpy as np
from kserve.protocol.infer_type import InferRequest, InferResponse
from kserve.protocol.grpc.grpc_predict_v2_pb2 import ModelInferResponse
from kserve import Model, ModelServer, model_server, InferRequest, InferOutput, InferResponse
from kserve import InferInput, InferRequest
from kserve.utils.utils import generate_uuid

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

def pre_process(data):
    print("pre_process:", data)
    return data

def model_data(data):
    data = data + 2 
    print("model_data:", data)
    return data

def post_process(data):
    data = data + 10
    print("post_process:", data)
    return data

# https://github.com/kserve/kserve/blob/master/docs/predict-api/v2/required_api.md#inference-request-json-object

class TransformerProcess(kserve.Model):
    
    def __init__(
            self,
            name: str,
            predictor_host: str,
            protocol: str = "v2",
        ):
        
        super().__init__(name)

        self.model_name = name

    def preprocess(self, request: InferRequest, headers: Dict[str, str] = None) -> Union[Dict, InferRequest]:
        input_tensors = [pre_process(instance) for instance in request.inputs[0].data]
        input_tensors = np.asarray(input_tensors, dtype=np.float32)
        infer_inputs = [
            InferInput(
                name="INPUT__0",
                datatype='FP32',
                shape=list(input_tensors.shape),
                data=input_tensors
            )
        ]
        infer_request = InferRequest(model_name=self.model_name, infer_inputs=infer_inputs)
        return infer_request

    def postprocess(self, response: InferResponse, headers: Dict[str, str] = None) -> Union[Dict, ModelInferResponse]:

        for infer_output in response.outputs:
            infer_output._data = post_process(infer_output.data)

        return super().postprocess(response, headers)
    
    def predict(self, input_tensor, headers: Dict[str, str] = None) -> Dict:

        input_tensors = [model_data(instance) for instance in input_tensor.inputs[0].data]
        input_tensors = np.asarray(input_tensors, dtype=np.float32)
        infer_output = InferOutput(
            name="output-0",
            shape=list(input_tensors.shape),
            datatype="FP32",
            data=input_tensors
        )

        response_id = generate_uuid()

        infer_response = InferResponse(model_name=self.name, infer_outputs=[infer_output], response_id=response_id)
      
        return infer_response
