import kserve
import argparse
from transform import TransformerProcess

DEFAULT_MODEL_NAME = "model"

parser = argparse.ArgumentParser(parents=[kserve.model_server.parser])

parser.add_argument(
    "--predictor_host", help="The URL for the model predict function",
    default="http://localhost:8080"
)
parser.add_argument(
    "--protocol", help="The protocol for the predictor", default="v2"
)
parser.add_argument(
    "--model_name", help="The name that the model is served under.",
    default=DEFAULT_MODEL_NAME
)
args, _ = parser.parse_known_args()

args, _ = parser.parse_known_args()

if __name__ == "__main__":
    transformer = TransformerProcess(
        args.model_name,
        predictor_host=args.predictor_host,
        protocol=args.protocol
    )
    server = kserve.ModelServer()
    server.start(models=[transformer])