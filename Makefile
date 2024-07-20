env := dev
build := $(shell date +%s)

ifdef profile
export AWS_PROFILE := $(profile)
endif

define param
$(shell yq -r ".$(1)" $(CURDIR)/application.yaml)
endef

install:
	pip3 install -r requirements-dev.txt -r requirements.txt

style:
	isort ./src/ ./tests/ -l 120 -m 3
	pylint ./src/ ./tests/ --rcfile=.pylintrc

test:
	PYTHONPATH='./src' pytest -v -p no:cacheprovider --disable-warnings ./tests/

build: clean
	python3 -m build

deploy: build
	$(MAKE) -C infrastructure/ $(@)

destroy:
	$(MAKE) -C infrastructure/ $(@)

clean:
	rm -rf ./.pytest_cache ./build ./dist ./src/*.egg-info

.PHONY: install style test build deploy destroy clean
