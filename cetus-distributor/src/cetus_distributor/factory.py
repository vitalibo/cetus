from pyxis.config import Config
from pyxis.pyspark import Job, Spark

from cetus_distributor.job import DistributionJob


def create_job(config: Config) -> Job:
    return DistributionJob(
        None,
        None,
        config)


def create_spark(config: Config) -> Spark:  # pylint: disable=unused-argument
    return Spark(None)
