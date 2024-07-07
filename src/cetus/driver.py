import logging
import sys

from pyxis.config import ConfigFactory

from cetus import factory


def main() -> None:
    """
    Main entry point for the application.
    """

    config = ConfigFactory.default_load()
    logging.basicConfig(**config.logging, stream=sys.stdout)
    logging.debug(config)

    try:
        job = factory.create_job(config)

        with factory.create_spark(config) as spark:
            spark.submit(job)
    except Exception as e:
        logging.error('unexpected error.', exc_info=e)
        raise e


if __name__ == '__main__':
    main()
