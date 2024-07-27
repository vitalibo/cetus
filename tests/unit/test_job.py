from unittest import mock

import pytest
from pyxis.config import ConfigFactory
from pyxis.resources import resource, resource_as_json

from cetus.job import DistributionJob


@pytest.mark.parametrize('case', [
    pytest.param(f'case{i}', id=f'Case #{i}: {item}') for i, item in enumerate([
        'empty dataframe',
        'one record',
        'two records - two files',
        'full dataset. no discarded values',
        'discarded values divisible by 3',
        'discarded values divisible by 4',
        'discarded values divisible by 4 and 6',
        'discarded values divisible by 4 and 3',
        'discarded values divisible by 4, 3, 5 and 7',
        'included only values 1, 24, 32, 46, 60, 61',
        'included only values 1,  -  32, 46, 60, 61. dropped dim1-a/dim2-b',
        'included only values 1, 24, 32, 46, 60,  -. resize cell length down',
        'included only values 1, 24, 32, 46, 60, 61, 62. resize cell length up',
        'two metrics',
        'two dimensions in body',

    ])
])
def test_job(case, spark):
    mock_lambda = mock.Mock()
    job = DistributionJob(
        spark.create_source_from_resource(
            __file__,
            f'data/test_job/{case}/source.json',
            'data/test_job/source.schema.json'),
        spark.create_sink_from_resource(
            __file__,
            f'data/test_job/{case}/sink.json',
            'data/test_job/sink.schema.json',
            order_by=('path',), ignore_schema=True),
        ConfigFactory.load(resource(
            __file__,
            f'data/test_job/{case}/config.json')),
        mock_lambda)

    spark.submit(job)

    mock_lambda.update_code.assert_called_once_with(
        resource_as_json(__file__, f'data/test_job/{case}/metadata.json'))
