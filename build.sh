# /bin/bash

python3 ./setup.py sdist bdist_wheel

twine upload ./dist/* -u danangjoyoo -p symbian29

rm -rf dist
rm -rf build
rm -rf worker.egg-info