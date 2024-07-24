import json

from pyxis.config import Config

from cetus.aws.cloudformation import Stack
from cetus.aws.lambda_func import LambdaFunction, code


class LambdaEdge:
    """
    LambdaEdge is an interface for updating code on AWS Lambda.
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def update_code(self, metadata: dict) -> None:
        code_str = code()
        code_str = code_str \
            .replace('{{ bucket }}', self.config.s3_bucket) \
            .replace('{{ metadata }}', json.dumps(metadata))

        func = LambdaFunction(self.config.function_name, self.config.s3_bucket)
        function_arn = func.update_function_code(code_str)

        stack = Stack(self.config.stack_name)
        stack.update(
            InterceptorFunctionVersion=function_arn
        )
