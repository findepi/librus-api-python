.PHONY: release
release:
	rm -rf dist/
	. .venv/bin/activate && \
	    pip install twine && \
	    ./setup.py sdist bdist_wheel && \
	    twine upload dist/*
