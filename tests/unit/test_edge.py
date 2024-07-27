import io
import os
import subprocess
import zipfile
from unittest import mock

from pyxis.config import Config

from cetus.edge import Distribution, LambdaEdge, LambdaFunction, Stack, code


@mock.patch('cetus.edge.code')
@mock.patch('cetus.edge.LambdaFunction')
@mock.patch('cetus.edge.Stack')
@mock.patch('cetus.edge.Distribution')
def test_update_code(mock_distribution, mock_stack, mock_lambda, mock_code):
    mock_lambda.return_value.update_function_code.return_value = 'arn..function:1'
    mock_stack.return_value.update.return_value = {'CloudFrontDistributionId': 'QWERTY'}
    mock_code.return_value = 'python_code {{ bucket }} {{ metadata }}'
    lambda_edge = LambdaEdge(Config({'bucket_name': 'foo', 'function_name': 'bar', 'stack_name': 'baz'}))

    lambda_edge.update_code({'foo': 'bar'})

    mock_lambda.assert_called_once_with('bar')
    mock_lambda.return_value.update_function_code.assert_called_once_with('python_code foo {"foo": "bar"}')
    mock_stack.assert_called_once_with('baz')
    mock_stack.return_value.update.assert_called_once_with(InterceptorFunctionVersion='arn..function:1')
    mock_distribution.assert_called_once_with('QWERTY')
    mock_distribution.return_value.invalidate.assert_called_once_with('/*')


@mock.patch('boto3.client')
def test_stack_update(mock_boto3):
    mock_cloudformation = mock.Mock()
    mock_waiter = mock.Mock()
    mock_cloudformation.get_waiter.return_value = mock_waiter
    mock_boto3.return_value = mock_cloudformation
    mock_cloudformation.describe_stacks.return_value = {
        'Stacks': [
            {
                'Parameters': [
                    {'ParameterKey': 'Parameter1', 'ParameterValue': 'old_value1'},
                    {'ParameterKey': 'Parameter2', 'ParameterValue': 'old_value2'},
                    {'ParameterKey': 'Parameter3', 'ParameterValue': 'old_value3'}
                ],
                'Outputs': [
                    {'OutputKey': 'Output1', 'OutputValue': 'output_value1'},
                    {'OutputKey': 'Output2', 'OutputValue': 'output_value2'}
                ]
            }
        ]
    }
    stack = Stack('my-stack')

    stack.update(Parameter1='value1', Parameter2='value2')

    mock_cloudformation.describe_stacks.assert_called_with(StackName='my-stack')
    mock_cloudformation.update_stack.assert_called_with(
        StackName='my-stack',
        UsePreviousTemplate=True,
        Parameters=[
            {'ParameterKey': 'Parameter1', 'ParameterValue': 'value1'},
            {'ParameterKey': 'Parameter2', 'ParameterValue': 'value2'},
            {'ParameterKey': 'Parameter3', 'ParameterValue': 'old_value3'}
        ],
        Capabilities=['CAPABILITY_NAMED_IAM']
    )
    mock_cloudformation.get_waiter.assert_called_with('stack_update_complete')
    mock_waiter.wait.assert_called_with(StackName='my-stack')
    mock_cloudformation.describe_stacks.assert_called_with(StackName='my-stack')


@mock.patch('boto3.client')
def test_distribution_invalidate(mock_boto3):
    mock_cloudfront = mock.Mock()
    mock_boto3.return_value = mock_cloudfront
    distribution = Distribution('foo')

    distribution.invalidate('/index.html', '/about.html')

    mock_cloudfront.create_invalidation.assert_called_once_with(
        DistributionId='foo',
        InvalidationBatch={
            'Paths': {
                'Quantity': 2,
                'Items': ['/index.html', '/about.html']
            },
            'CallerReference': mock.ANY
        }
    )


@mock.patch('boto3.client')
def test_lambda_update_function_code(mock_boto3):
    mock_client = mock_boto3.return_value
    mock_client.update_function_code.return_value = {
        'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:my-function'
    }
    function = LambdaFunction('my-function')

    actual = function.update_function_code('print("Hello, World!")')

    assert actual == 'arn:aws:lambda:us-east-1:123456789012:function:my-function'
    call_args = mock_client.update_function_code.call_args
    assert call_args.kwargs['FunctionName'] == 'my-function'
    assert call_args.kwargs['Publish'] is True
    with zipfile.ZipFile(io.BytesIO(call_args.kwargs['ZipFile'])) as archive:
        with archive.open('index.py') as file:
            assert file.read().decode('utf-8') == 'print("Hello, World!")'


def test_code():
    subprocess.run(
        ['make', 'build'],
        cwd=os.path.join(os.path.dirname(__file__), '../../'),
        check=True)

    actual = code()

    assert 'def handler(event, context):' in actual
