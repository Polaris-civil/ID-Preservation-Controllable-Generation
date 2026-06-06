.PHONY: install dev test demo workflow clean

install:
	python -m pip install -e .

dev:
	python -m pip install -e .

test:
	python -m unittest discover -s tests

demo:
	python examples/run_demo.py

workflow:
	idpcg workflow --output outputs/comfyui_workflow.json

clean:
	rm -rf outputs checkpoints build dist *.egg-info .pytest_cache
