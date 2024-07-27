import json

from pyxis.config import Config

from cetus.aws.cloudformation import Stack
from cetus.aws.cloudfront import Distribution
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
            .replace('{{ bucket }}', self.config.bucket_name) \
            .replace('{{ metadata }}', json.dumps(metadata))

        func = LambdaFunction(self.config.function_name)
        function_arn = func.update_function_code(code_str)

        stack = Stack(self.config.stack_name)
        outputs = stack.update(
            InterceptorFunctionVersion=function_arn
        )

        cloudfront = Distribution(outputs['CloudFrontDistributionId'])
        cloudfront.invalidate('/*')
