.PHONY: release
release:
	rm -rf dist/
	. .venv/bin/activate && \
	    pip install setuptools twine wheel && \
	    ./setup.py sdist bdist_wheel && \
	    twine upload dist/*
