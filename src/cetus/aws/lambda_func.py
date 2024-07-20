import io
import os
import zipfile

import boto3


def code():
    file = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '../../../dist/cetus-0.1.0-py3-none-any.whl'))
    if '.whl' in __file__:
        file = __file__.split('whl')[0] + 'whl'

    if not os.path.exists(file):
        raise FileNotFoundError(file)

    with zipfile.ZipFile(file, 'r') as archive:
        with archive.open('cetus/lambda.py') as file:
            return file.read().decode('utf-8')


class LambdaFunction:
    """
    Manage AWS Lambda function.
    """

    def __init__(self, function_name: str, bucket: str) -> None:
        self._client = boto3.client('lambda')
        self.function_name = function_name
        self.bucket = bucket

    def update_function_code(self, code: str) -> str:
        """
        Update AWS Lambda function code.

        :param code: source code
        :return: function ARN
        """

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('index.py', code.encode('utf-8'))

        response = self._client.update_function_code(
            FunctionName=self.function_name,
            ZipFile=buffer.getvalue(),
            Publish=True
        )

        return response['FunctionArn']
