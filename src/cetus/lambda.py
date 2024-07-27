import json
import logging
import math

import boto3

s3 = boto3.resource('s3')

metadata = json.loads('{{ metadata }}')
cols, length = metadata['cols'], metadata['length']


def handler(event, context):  # pylint: disable=unused-argument
    """
    AWS Lambda@Edge handler.

    :param event: CloudFront origin request event
    :param context: Lambda context
    :return: response object
    """

    url = event['Records'][0]['cf']['request']['uri']
    params = url.split('/')
    offset = content_offset(*params[len(cols) + 1:])

    if offset == -1:
        return response(404, 'Not Found')

    try:
        body = (
            s3.Object('{{ bucket }}', '/'.join(params[:len(cols) + 1])[1:])
            .get(Range=f'bytes={offset * length}-{(offset + 1) * length - 1}')['Body']
            .read()
            .decode('utf-8')
            .rstrip(' ')
        )

        return response(200, 'OK', body=body)
    except Exception as e:  # pylint: disable=broad-except
        logging.error(e)
        return response(404, 'Not Found')


def response(status, status_description, body=None):
    """
    Create a response object.

    :param status: HTTP status code
    :param status_description: HTTP status description
    :param body: Optional response body. If not provided, a default message will be returned.
    :return: response object
    """

    return {
        'status': status,
        'statusDescription': status_description,
        'headers': {
            'content-type': [
                {
                    'key': 'Content-Type',
                    'value': 'application/json',
                }
            ]
        },
        'body': (
            body
            if body else
            json.dumps({
                'status': status,
                'message': status_description
            })
        )
    }


def content_offset(*params):
    """
    Calculate the offset of the content to be returned based on the URL parameters.

    :param params: URL parameters
    :return: offset of the content to be returned
    """

    try:
        return sum(
            cols[str(i)][param] * math.prod([len(j) for j in cols.values()][i + 1:])
            for i, param in enumerate(params)
        )
    except KeyError:
        return -1
