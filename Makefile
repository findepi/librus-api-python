.PHONY: release
release:
	rm -rf dist/
	. .venv/bin/activate && \
	    ./setup.py sdist bdist_wheel && \
	    twine upload dist/*
