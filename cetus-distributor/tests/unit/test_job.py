import pytest
from pyxis.config import ConfigFactory
from pyxis.resources import resource

from cetus_distributor.job import DistributionJob


@pytest.mark.parametrize('case', [
    pytest.param(f'case{i}', id=f'Case #{i}: {item}') for i, item in enumerate([
        'empty dataframe',
    ])
])
def test_job(case, spark):
    job = DistributionJob(
        spark.create_source_from_resource(
            __file__,
            f'data/{case}/source.json',
            f'data/source.schema.json'),
        spark.create_sink_from_resource(
            __file__,
            f'data/{case}/sink.json',
            f'data/sink.schema.json'),
        ConfigFactory.load(resource(
            __file__,
            f'data/{case}/config.yaml')))

    spark.submit(job)
