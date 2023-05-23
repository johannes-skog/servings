import kserve
from typing import List, Dict, Union
import logging
import numpy as np
from kserve.protocol.infer_type import InferRequest, InferResponse, InferInput, InferOutput
from kserve.protocol.grpc.grpc_predict_v2_pb2 import ModelInferResponse
# from kserve import Model, ModelServer, model_server, InferRequest, InferOutput, InferResponse
# from kserve import InferInput, InferRequest
from kserve.utils.utils import generate_uuid

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

"""
logger = logging.getLogger("jes")

# Set the log level (e.g., INFO, DEBUG, WARNING)
logger.setLevel(logging.INFO)

# Create a file handler to write logs to a file
file_handler = logging.FileHandler('transformer.log')

# Create a formatter to specify the log message format
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# Set the formatter for the file handler
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
"""

def pre_process(data):
    
    data = np.asarray(data).astype(np.float32)
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
# https://github.com/kserve/kserve/blob/0ba642f9b6fa40b38fe272d04c8dfde3598bfb05/python/kserve/kserve/protocol/infer_type.py#L334


class TransformerProcess(kserve.Model):

    REQUEST_ID = "x-request-id"
    
    def __init__(
            self,
            name: str,
            predictor_host: str,
            protocol: str = "v2",
        ):
        
        logging.info(f"Predictor host:{predictor_host}")
        logging.info(f"Protocol:{protocol}")
        
        super().__init__(name)

        self.predictor_host = predictor_host
        self.protocol = protocol
        self.model_name = name
        self.ready = True

    def _get_id(self, headers: Dict[str, str]) -> str:
        return headers.get(TransformerProcess.REQUEST_ID, generate_uuid())

    async def preprocess(self, request: InferRequest, headers: Dict[str, str] = None) -> Union[Dict, InferRequest]:

        request_id = self._get_id(headers)
        
        logging.info(f"Preprocess request:{request_id}")

        # Do preprocessing here, handle the different input types differently 
        for infer_input in request.inputs:
            if infer_input.name == "INPUT__0":
                infer_input._data  = pre_process(infer_input.data)
            else:
                pass

        infer_request = InferRequest(
            model_name=self.model_name,
            infer_inputs=request.inputs,
            request_id=request_id
        )

        return infer_request

    def postprocess(self, response: InferResponse, headers: Dict[str, str] = None) -> Union[Dict, ModelInferResponse]:
        
        logging.info(f"Postprocess request:{response.id}")

        for infer_output in response.outputs:
            infer_output._data = np.reshape(infer_output.data, infer_output.shape)
            infer_output._data = post_process(infer_output.data).tolist()

        infer_output.parameters["EXTRA"] = "EXTRA"

        return super().postprocess(response, headers)

    async def predict(self, input_tensor, headers: Dict[str, str] = None) -> Dict:

        infer_response_dict = await super().predict(input_tensor, headers) 

        infer_outputs = []

        for infer_output in infer_response_dict["outputs"]:

            infer_output = InferOutput(
                name=infer_output["name"],
                shape=infer_output["shape"],
                datatype=infer_output["datatype"],
                data=infer_output["data"]
            )

            infer_outputs.append(infer_output)

        infer_response = InferResponse(
            model_name=infer_response_dict["model_name"],
            infer_outputs=infer_outputs,
            response_id=self._get_id(headers)
        )
        
        return infer_response
    
    """

    def predict(self, input_tensor, headers: Dict[str, str] = None) -> Dict:

        # Choose which inputs to use for prediction, filter on the name, i.e. input_tensor.inputs[0].name
        input_tensors = [model_data(instance) for instance in input_tensor.inputs[0].data]
        input_tensors = np.asarray(input_tensors, dtype=np.float32)
        
        print("predict input_tensors:", input_tensors.shape, input_tensors.dtype)

        infer_output = InferOutput(
            name="output-0",
            shape=list(input_tensors.shape),
            datatype="FP32",
            data=input_tensors
        )

        response_id = self._get_id(headers)

        infer_response = InferResponse(model_name=self.name, infer_outputs=[infer_output], response_id=response_id)
      
        return infer_response
    """