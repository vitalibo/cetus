from unittest import mock

from cetus.io import S3BlobFileSink, S3Source


def test_s3_source():
    mock_spark = mock.Mock()
    mock_spark_session = mock.Mock()
    mock_dataframe = mock.Mock()
    mock_spark_session.read.load.return_value = mock_dataframe
    mock_spark.spark_session = mock_spark_session
    source = S3Source(bucket='bucket', path='path')

    actual = source.extract(mock_spark)

    assert actual == mock_dataframe
    mock_spark_session.read.load.assert_called_once_with(bucket='bucket', path='path')


@mock.patch('boto3.Session')
def test_s3_blob_file_sink(mock_session):
    mock_boto3_session = mock.Mock()
    mock_session.return_value = mock_boto3_session
    mock_s3 = mock.Mock()
    mock_bucket = mock.Mock()
    mock_s3.Bucket.return_value = mock_bucket
    mock_boto3_session.resource.return_value = mock_s3
    mock_dataframe = mock.Mock()
    mock_dataframe.foreachPartition.side_effect = lambda f: f([
        {'path': 'file1', 'file': '{json1}'},
        {'path': 'file2', 'file': '{json2}'}
    ])
    sink = S3BlobFileSink('foo')

    sink.load(None, mock_dataframe)

    mock_dataframe.foreachPartition.assert_called_once()
    mock_session.assert_called_once()
    mock_boto3_session.resource.assert_called_once_with('s3')
    mock_s3.Bucket.assert_called_once_with('foo')
    mock_bucket.put_object.assert_has_calls([
        mock.call(Key='file1', Body='{json1}'),
        mock.call(Key='file2', Body='{json2}')
    ])
