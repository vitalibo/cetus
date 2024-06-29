import pytest
from pyxis.config import ConfigFactory
from pyxis.resources import resource

from cetus_distributor.job import DistributionJob


@pytest.mark.parametrize('case', [
    pytest.param(f'case{i}', id=f'Case #{i}: {item}') for i, item in enumerate([
        'empty dataframe',
        'one row one file',
        'two rows one two files',
    ])
])
def test_job(case, spark):
    job = DistributionJob(
        spark.create_source_from_resource(
            __file__,
            f'data/{case}/source.json',
            'data/source.schema.json'),
        spark.create_sink_from_resource(
            __file__,
            f'data/{case}/sink.json',
            'data/sink.schema.json',
            order_by=('path',)),
        ConfigFactory.load(resource(
            __file__,
            f'data/{case}/config.yaml')))

    spark.submit(job)
