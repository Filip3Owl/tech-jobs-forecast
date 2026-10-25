.PHONY: install test notebooks all clean

NOTEBOOKS := $(sort $(wildcard notebooks/0*.ipynb))

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest -q

notebooks:
	@for nb in $(NOTEBOOKS); do \
		echo "Executando $$nb"; \
		jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 $$nb || exit 1; \
	done

all: test notebooks

clean:
	rm -rf data/raw/*.csv data/raw/*.json data/processed/*.csv .pytest_cache
