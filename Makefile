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

package: build
	PYTHONPATH='./src' MAKEOVERRIDES= python3 ./src/cetus/cdk/synthesizer.py --env $(env) --stack distributor --build $(build)

deploy: package
	@echo 'Uploading assets to S3...'
	@jq '[.files | to_entries[] | [.value.source.path, .value.destinations."current_account-current_region".bucketName, .value.destinations."current_account-current_region".objectKey]]' cdk.out/Stack.assets.json | \
		jq -r '.[] | @tsv' | while IFS=$$'\t' read -r src bucket dest; do \
		aws s3 cp "./cdk.out/$$src" "s3://$$bucket/$$dest" ; \
	done

	aws cloudformation deploy \
		--stack-name "$(call param,name)-$(env)-distributor" \
		--capabilities CAPABILITY_NAMED_IAM \
		--template-file ./cdk.out/Stack.template.json \
		--tags Environment=$(env) CostCenter='data-platform' Application='$(call param,name)'

clean:
	rm -rf ./.pytest_cache ./build ./dist ./src/*.egg-info ./cdk.out

.PHONY: install style test build package deploy clean
