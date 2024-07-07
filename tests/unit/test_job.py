from unittest import mock

import pytest
from pyxis.config import ConfigFactory
from pyxis.resources import resource, resource_as_json

from cetus.job import DistributionJob


@pytest.mark.parametrize('case', [
    pytest.param(f'case{i}', id=f'Case #{i}: {item}') for i, item in enumerate([
        'empty dataframe',
        'one row one file',
        'two rows one two files',
    ])
])
def test_job(case, spark):
    mock_lambda = mock.Mock()
    job = DistributionJob(
        spark.create_source_from_resource(
            __file__,
            f'data/{case}/source.json',
            'data/source.schema.json'),
        spark.create_sink_from_resource(
            __file__,
            f'data/{case}/sink.json',
            'data/sink.schema.json',
            order_by=('path',), ignore_schema=True),
        ConfigFactory.load(resource(
            __file__,
            f'data/{case}/config.json')),
        mock_lambda)

    spark.submit(job)

    mock_lambda.update_code.assert_called_once_with(
        resource_as_json(__file__, f'data/{case}/metadata.json'))
