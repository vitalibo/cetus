from functools import reduce

from pyspark.sql import functions as fn
from pyxis.config import Config
from pyxis.pyspark import Job, Sink, Source, Spark

from cetus_distributor.edge import LambdaEdge


class DistributionJob(Job):
    """
    Job group data into files and save them to S3.
    """

    def __init__(
            self,
            source: Source,
            sink: Sink,
            config: Config,
            lambda_edge: LambdaEdge
    ) -> None:
        self.source = source
        self.sink = sink
        self.config = config
        self.lambda_edge = lambda_edge

    def transform(self, spark: Spark) -> None:
        dimensions, metrics = self.config.dimensions, self.config.metrics

        df = spark.extract(self.source)

        df = df \
            .withColumn('version', fn.lit(self.config.version)) \
            .fillna('Unknown', dimensions.path + dimensions.file + dimensions.body) \
            .withColumn('path', fn.array_join(fn.array('version', *dimensions.path), '/')) \
            .withColumn('_1', fn.transform(fn.array(*metrics), lambda o: fn.round(o, self.config.scale)))

        for i in range(len(dimensions.body)):
            df = df \
                .groupby('path', *dimensions.file, *dimensions.body[:-i - 1]) \
                .agg(fn.map_from_arrays(fn.collect_list(dimensions.body[-i - 1]), fn.collect_list('_1')).alias('_1'))

        df = df \
            .withColumn('body', fn.to_json('_1')) \
            .cache()

        file_cols = [df.select(i).distinct() for i in dimensions.file]

        df = df \
            .join(reduce(lambda a, b: a.crossJoin(b), file_cols), dimensions.file, 'full_outer') \
            .fillna('{}', 'body') \
            .cache()

        length = df \
            .groupby() \
            .agg(fn.max(fn.length(df.body))) \
            .collect()[0][0]

        df = df \
            .withColumn('body', fn.rpad(df.body, length or 0, ' ')) \
            .groupby(df.path) \
            .agg(fn.collect_list(fn.struct(*dimensions.file, 'body')).alias('file')) \
            .withColumn('file', fn.array_join(fn.transform(fn.sort_array('file'), lambda x: x.body), ''))

        spark.load(self.sink, df)

        self.lambda_edge.update_code({
            'cols': {
                str(i): {value: j for j, value in enumerate(sorted([row[0] for row in values.collect()]))}
                for i, values in enumerate(file_cols)
            },
            'length': length
        })
