.PHONY: test demo build clean

test:
	python -m pytest tests/ -v

build:
	python main.py build examples/mnist.tml

demo:
	python main.py tokens examples/mnist.tml
	python main.py parse examples/mnist.tml --trace
	python main.py tables
	python main.py ast examples/mnist.tml
	python main.py semantic examples/mnist.tml
	python main.py ir examples/mnist.tml --opt
	python main.py memory examples/mnist.tml
	python main.py build examples/mnist.tml
	python main.py verify examples/mnist.tml

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').glob('**/__pycache__')]; [p.unlink() for p in pathlib.Path('.').glob('**/*.pyc')]"
