import json
import math

import boto3

s3 = boto3.resource('s3')

metadata = json.loads('{{ metadata }}')

columns = metadata['columns']
length = metadata['length']


def handler(event, context):  # pylint: disable=unused-argument
    url = event['Records'][0]['cf']['request']['uri']
    params = url.split('/')
    offset = body_offset(*params[len(columns):])

    if offset == -1:
        return {
            'status': 404,
            'statusDescription': 'Not Found',
            'body': 'Not found'
        }

    obj = s3.Object('{{ bucket }}', '/'.join(params[:len(columns)]))
    body = (
        obj.get(Range=f'bytes={offset * length + offset}-{(offset + 1) * length + offset}')['Body']
        .read()
        .decode('utf-8')
        .rstrip(' ')
    )

    return {
        'status': 200,
        'statusDescription': 'OK',
        'headers': {
            'content-type': [
                {
                    'key': 'Content-Type',
                    'value': 'application/json',
                }
            ]
        },
        'body': body
    }


def body_offset(*params):
    try:
        return sum(
            columns[i][param] * math.prod([len(j) for j in columns.values()][i + 1:])
            for i, param in enumerate(params)
        )
    except KeyError:
        return -1
