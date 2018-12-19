mkdir libraries
cd libraries
pip install -r ../requirements/prod.txt --target .
zip -r ../function.zip .
cd ..
zip -g function.zip function.py
