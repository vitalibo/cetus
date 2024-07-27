from pyspark import SparkConf
from pyspark.sql import SparkSession
from pyxis.config import Config
from pyxis.pyspark import Job, Spark

from cetus.edge import LambdaEdge
from cetus.io import S3BlobFileSink, S3Source
from cetus.job import DistributionJob


def create_job(config: Config) -> Job:
    """
    Create a Job instance.
    """

    return DistributionJob(
        S3Source(**dict(config.source)),
        S3BlobFileSink(config.infra.bucket_name),
        config.transform,
        LambdaEdge(config.infra))


def create_spark(config: Config) -> Spark:
    """
    Create a Spark instance.
    """

    spark_conf = SparkConf()
    properties = dict(config.get('spark.properties', {}))
    for key, value in properties.items():
        spark_conf.set(key, value)

    spark_session = SparkSession.builder \
        .config(conf=spark_conf) \
        .getOrCreate()

    return Spark(spark_session)
