import importlib
from io import BytesIO
from unittest import mock

import pytest


@mock.patch('boto3.resource')
@mock.patch('json.loads')
@pytest.mark.parametrize('params, expected_range', [
    ('Africa/2020/1', 'bytes=0-3'),
    ('Africa/2020/2', 'bytes=4-7'),
    ('Asia/2022/2', 'bytes=84-87'),
    ('Europe/2022/2', 'bytes=132-135')
])
def test_handler(mock_json_loads, mock_session, params, expected_range):
    mock_s3 = mock.Mock()
    mock_session.return_value = mock_s3
    mock_obj = mock.Mock()
    mock_obj.get.return_value = {'Body': BytesIO(b'{"value": 1}     ')}
    mock_s3.Object.return_value = mock_obj
    url = f'/Toys/Holiday_Sale/{params}'
    mock_json_loads.return_value = {
        'version': 'v1',
        'length': 3,
        'columns': {
            0: {'Africa': 0, 'Asia': 1, 'Europe': 2, 'North America': 3, 'South America': 4},
            1: {'2020': 0, '2021': 1, '2022': 2},
            2: {'1': 0, '2': 1, '3': 2, '4': 3}
        }
    }

    aws_lambda = importlib.import_module('cetus_interceptor.lambda')
    importlib.reload(aws_lambda)
    actual = aws_lambda.handler(create_event(url), mock.Mock())

    assert actual == {
        'status': 200,
        'statusDescription': 'OK',
        'headers': {
            'content-type': [
                {
                    'key': 'Content-Type',
                    'value': 'application/json'
                }
            ]
        },
        'body': '{"value": 1}'
    }
    mock_s3.Object.assert_called_once_with('{{ bucket }}', '/Toys/Holiday_Sale')
    mock_obj.get.assert_called_once_with(Range=expected_range)


def create_event(url):
    return {
        'Records': [
            {
                'cf': {
                    'config': {
                        'distributionDomainName': 'd111111abcdef8.cloudfront.net'
                    },
                    'request': {
                        'method': 'GET',
                        'querystring': '',
                        'uri': url
                    }
                }
            }
        ]
    }
