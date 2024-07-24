import boto3
from pyspark.sql import DataFrame
from pyxis.pyspark import Sink, Source, Spark


class S3Source(Source):
    """
    Source to read files from S3 bucket.
    """

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def extract(self, spark: Spark, *args, **kwargs) -> DataFrame:
        return spark.spark_session.read.load(**self.kwargs)


class S3BlobFileSink(Sink):
    """
    Sink to write files to S3 bucket.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def load(self, spark: Spark, df: DataFrame, *args, **kwargs) -> None:
        def batch_write(iterator):
            boto3_session = boto3.Session()
            s3 = boto3_session.resource('s3')
            bucket = s3.Bucket(self.bucket)
            for row in iterator:
                bucket.put_object(Key=row['path'], Body=row['file'])

        df.foreachPartition(batch_write)
