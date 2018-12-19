
import requests
import datetime
import logging
import logging.handlers
import boto3
import botocore

log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s(%(levelname)s) %(message)s')
log.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        timestamp = str(datetime.datetime.now().strftime("%Y%m%dT%H%M%S"))
        filename = timestamp + '.csv'
        data = convert(download_data(), timestamp)
        save_to_s3(data, filename)
        log.info('Success {}'.format(filename))

    except requests.exceptions.RequestException as e:
        log.info('Fetch failed: {} {}'.format(type(e), str(e)))
        return
    except botocore.exceptions.ClientError as e:
        log.info('AWS error writing file to bucket: {} {}'.format(type(e), str(e)))
        return


def download_data():
    result = requests.get('http://www.tanczos.com/tanczos.com/beerinventory/webexport.csv')
    # Force utf-8.  It goes to ISO-8859-1 (Latin)
    result.encoding = 'utf-8'
    return result.text


def save_to_s3(data, filename):
    s3 = boto3.resource('s3')
    file_object = s3.Object('tanczos-data', filename)
    file_object.put(Body=data)


def convert(inventory_data, timestamp):
    """
    Computes a modified version of the data in the given filename:

    1. Remove the BOM (Byte-order mark), if present
    2. Take the timestamp from the filename and add it as a
       Column in every row

    :param inventory_data: the pathname to a filename in the form YYYY-MM-DD_HH:MM:SS.FFFFF.csv
    :param timestamp: the timestamp to add to each line of the data
    :return: a string containing the converted contents
    """
    ret = ''

    lines = inventory_data.split('\n')
    headers = lines.pop(0)

    # Remove the BOM if present.  The download process forced
    # utf-8 encoding, so this will work.
    if headers.startswith('\ufeff'):
        headers = headers[1:]

    headers = headers.strip()
    ret += '{},"timestamp"\n'.format(headers)

    for line in lines:
        line = line.strip()
        if line == '':
            continue
        ret += '{},"{}"\n'.format(line, timestamp)

    return ret


if __name__ == '__main__':
    lambda_handler(0, 0)
