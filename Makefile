.PHONY:test
test: clean
	nosetests -v app
	./script/check-pep8.sh app/
	./script/check-todo.sh app/

.PHONY: clean
clean:
	find . -iname '*.pyc' -delete
	find . -name __pycache__ -type d -delete
	rm -f .coverage

