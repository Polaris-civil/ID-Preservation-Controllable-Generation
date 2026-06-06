.PHONY: install dev test demo workflow clean

install:
	uv sync

dev:
	uv sync --extra dev

test:
	uv run python -m unittest discover -s tests

demo:
	uv run python examples/run_demo.py

workflow:
	uv run idpcg workflow --output outputs/comfyui_workflow.json

clean:
	rm -rf outputs checkpoints build dist *.egg-info .pytest_cache
