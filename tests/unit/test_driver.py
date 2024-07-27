from unittest import mock

import pytest
from pyxis.config import Config

from cetus.driver import main


@mock.patch('pyxis.config.ConfigFactory.default_load')
@mock.patch('cetus.driver.factory')
def test_main(mock_factory, mock_config_factory_default_load):
    mock_config_factory_default_load.return_value = Config({'logging': {'level': 'INFO', }})
    mock_job = mock.Mock()
    mock_factory.create_job.return_value = mock_job
    mock_spark = mock.MagicMock()
    mock_spark.__enter__.return_value = mock_spark
    mock_factory.create_spark.return_value = mock_spark

    main()

    mock_config_factory_default_load.assert_called_once()
    mock_factory.create_job.assert_called_once()
    mock_factory.create_spark.assert_called_once()
    mock_spark.__enter__.assert_called_once()
    mock_spark.submit.assert_called_once_with(mock_job)
    mock_spark.__exit__.assert_called_once()


@mock.patch('pyxis.config.ConfigFactory.default_load')
@mock.patch('cetus.driver.factory')
def test_main_error(mock_factory, mock_config_factory_default_load):
    mock_config_factory_default_load.return_value = Config({'logging': {'level': 'INFO', }})
    mock_job = mock.Mock()
    mock_factory.create_job.return_value = mock_job
    mock_spark = mock.MagicMock()
    mock_spark.submit.side_effect = Exception('error')
    mock_spark.__enter__.return_value = mock_spark
    mock_factory.create_spark.return_value = mock_spark

    with pytest.raises(Exception):
        main()

    mock_config_factory_default_load.assert_called_once()
    mock_factory.create_job.assert_called_once()
    mock_factory.create_spark.assert_called_once()
    mock_spark.__enter__.assert_called_once()
    mock_spark.submit.assert_called_once_with(mock_job)
    mock_spark.__exit__.assert_called_once()
