lint:
	pycodestyle --statistics Tea/  --max-line-length=100 --ignore=W391,E121,E123,E126,E226,E24,E704,W503,W504 --exclude=vendored

test:
	pytest tests/
