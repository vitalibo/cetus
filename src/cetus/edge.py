import io
import json
import logging
import os
import zipfile
from datetime import datetime

import boto3
from pyxis.config import Config


class LambdaEdge:
    """
    LambdaEdge is an interface for updating code on AWS Lambda.
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def update_code(self, metadata: dict) -> None:
        if metadata['length'] is None:
            logging.info('nothing to update')
            return

        code = source_code() \
            .replace('{{ bucket }}', self.config.bucket_name) \
            .replace('{{ metadata }}', json.dumps(metadata))

        function = LambdaFunction(self.config.function_name)
        function_arn = function.update_function_code(code)

        stack = Stack(self.config.stack_name)
        outputs = stack.update(InterceptorFunctionVersion=function_arn)

        cloudfront = Distribution(outputs['CloudFrontDistributionId'])
        cloudfront.invalidate('/*')


class Stack:
    """
    Class for managing CloudFormation stacks.
    """

    def __init__(self, stack_name: str):
        self._client = boto3.client('cloudformation')
        self.stack_name = stack_name

    def update(self, **kwargs) -> dict[str, str]:
        """
        Updates a stack with new parameters values and waits for the update to complete.

        :param kwargs: The new parameters values.
        :return: None
        """

        parameters = self._client.describe_stacks(StackName=self.stack_name)['Stacks'][0]['Parameters']
        parameters = {o['ParameterKey']: o['ParameterValue'] for o in parameters}
        parameters.update(kwargs)

        self._client.update_stack(
            StackName=self.stack_name,
            UsePreviousTemplate=True,
            Parameters=[
                {
                    'ParameterKey': k,
                    'ParameterValue': v
                } for k, v in parameters.items()
            ],
            Capabilities=[
                'CAPABILITY_NAMED_IAM'
            ]
        )

        logging.info('Waiting for stack update to complete')
        waiter = self._client.get_waiter('stack_update_complete')
        waiter.wait(StackName=self.stack_name)
        logging.info('Successfully updated stack')

        outputs = self._client.describe_stacks(StackName=self.stack_name)['Stacks'][0]['Outputs']
        return {
            output['OutputKey']: output['OutputValue']
            for output in outputs
        }


class Distribution:
    """
    Class for managing CloudFront distributions.
    """

    def __init__(self, distribution_id: str) -> None:
        self._client = boto3.client('cloudfront')
        self.distribution_id = distribution_id

    def invalidate(self, *paths) -> None:
        """
        Invalidates the specified paths in the CloudFront distribution.

        :param paths: The paths to invalidate.
        :return: None
        """

        self._client.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': list(paths)
                },
                'CallerReference': datetime.now().strftime('Cetus-%Y%m%d%H%M%S')
            }
        )


class LambdaFunction:
    """
    Manage AWS Lambda function.
    """

    def __init__(self, function_name: str) -> None:
        self._client = boto3.client('lambda')
        self.function_name = function_name

    def update_function_code(self, src_code: str) -> str:
        """
        Update AWS Lambda function code.

        :param src_code: source code
        :return: function ARN
        """

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('index.py', src_code.encode('utf-8'))

        response = self._client.update_function_code(
            FunctionName=self.function_name,
            ZipFile=buffer.getvalue(),
            Publish=True
        )

        return response['FunctionArn']


def source_code():
    file = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '../../dist/cetus-0.1.0-py3-none-any.whl'))
    if '.whl' in __file__:
        file = __file__.split('whl', maxsplit=1)[0] + 'whl'

    if not os.path.exists(file):
        raise FileNotFoundError(file)

    with zipfile.ZipFile(file, 'r') as archive:
        with archive.open('cetus/lambda.py') as file:
            return file.read().decode('utf-8')
