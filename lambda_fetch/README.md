
## Development

### Setup

* Create a virtual environment and install the requirements: `pip install -r requirements/dev.txt`)

* Run tests: `pytest`

### Deploy

* The script `makezip.sh` will create a zip file that contains the production libraries and the source code for the lambda function.
* Upload using the AWS CLI: `aws lambda update-function-code --function-name FetchBeerInventory --zip-file fileb://function.zip`  This step requires credentials in the moco-csdev account.
