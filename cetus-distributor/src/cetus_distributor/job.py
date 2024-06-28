from pyxis.config import Config
from pyxis.pyspark import Job, Source, Sink, Spark


class DistributionJob(Job):

    def __init__(
            self,
            source: Source,
            sink: Sink,
            config: Config
    ) -> None:
        self.source = source
        self.sink = sink
        self.config = config

    def transform(self, spark: Spark) -> None:
        df = spark.extract(self.source)

        spark.load(self.sink, df)
