
import function
from unittest.mock import MagicMock
import moto
import boto3
import botocore
import requests_mock
import requests
import pytest


@pytest.fixture()
def tanczos_bucket():
    # This code will "wrap" the tests where the fixture is used,
    # Causing all boto3 calls to be mocked.
    with moto.mock_s3():
        s3 = boto3.resource('s3')
        s3.create_bucket(Bucket='tanczos-data')
        yield s3.Bucket('tanczos-data')


def test_convert_removes_BOM():
    with open('test_files/bom.csv') as f:
        data = f.read()
        result = function.convert(data, "20181218T174633")
        assert data.startswith('\ufeff')
        assert not result.startswith('\ufeff')


def test_convert_no_bom():
    with open('test_files/nobom.csv') as f:
        data = f.read()
        result = function.convert(data, "20181218T174633")
        assert not result.startswith('\ufeff')


def test_failed_connection_logged(caplog, tanczos_bucket):
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, exc=requests.exceptions.RequestException)
        function.lambda_handler(0, 0)
        # caplog is built into pytest and captures logs
        assert 'Fetch failed' in caplog.text

    # no file written to s3 bucket
    assert len(list(tanczos_bucket.objects.all())) == 0


def test_success_adds_one_file(caplog, tanczos_bucket):
    #fetch.download_data = MagicMock(return_value= open('test_files/bom.csv').read())
    with requests_mock.Mocker() as m:
        m.get(requests_mock.ANY, text=open('test_files/bom.csv').read())
        function.lambda_handler(0, 0)
        assert len(list(tanczos_bucket.objects.all())) == 1
        assert "Success" in caplog.text

    # UGH, getting the contents of a file is not easy
    s3 = boto3.resource('s3')
    for key in tanczos_bucket.objects.all():
        # YYYYMMDDTHHMMSS.csv is 19 characters
        assert len(key.key) == 19
        obj = s3.Object('tanczos-data', key.key)
        text = obj.get()['Body'].read().decode('utf-8')
        lines = text.split('\n')
        # last entry is empty because we split on \n
        lines.pop()
        headers = lines.pop(0).split(',')
        assert 'Name' in headers[0]
        assert 'timestamp' in headers[-1]
        for line in lines:
            assert len(line.split(',')) == 8


def test_failed_s3_interaction_logged(caplog, tanczos_bucket):
    function.download_data = MagicMock(return_value=open('test_files/bom.csv').read())

    response = {'Error': {'Code': '403', 'Message': 'Fake Exception'}}
    function.save_to_s3 = MagicMock(side_effect=botocore.exceptions.ClientError(response, 'get'))

    function.lambda_handler(0, 0)
    assert len(list(tanczos_bucket.objects.all())) == 0
    assert "AWS error" in caplog.text
