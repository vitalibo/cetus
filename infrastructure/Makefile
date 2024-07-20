environment :=
profile :=

ifeq ($(filter /$(environment),$(shell find ./stages -type f -name '*.yaml' | cut -c 9-  | rev | cut -c 6- | rev | paste -sd " " - | xargs)),)
    $(error environment '$(environment)' is not supported)
endif

ifdef profile
export AWS_PROFILE := $(profile)
endif

define param
$(shell yq -r ".Parameters.$(1)" $(CURDIR)/stages/$(environment).yaml)
endef

define params
$(shell yq -r '.$(1) | to_entries | map(.key + "=" + .value) | join(" ")' $(CURDIR)/stages/$(environment).yaml)
endef

deploy:
	@ \
	ScriptLocation='s3://$(call param,Bucket)/$(call param,Unit)/$(call param,Environment)/$(call param,Name)/$(shell date +%s)/'; \
	\
	echo 'Waiting for the assets to be uploaded...'; \
	aws s3 cp $(CURDIR)/../src/cetus/driver.py $${ScriptLocation}; \
	aws s3 cp $(CURDIR)/../application.yaml $${ScriptLocation}; \
	aws s3 cp $(CURDIR)/../dist/cetus-0.1.0-py3-none-any.whl $${ScriptLocation}; \
	\
	aws cloudformation deploy \
		--stack-name '$(call param,Unit)-$(call param,Environment)-$(call param,Name)-infra' \
		--capabilities 'CAPABILITY_NAMED_IAM' \
		--parameter-overrides $(call params,Parameters) \
			ScriptLocation=$${ScriptLocation} \
			AdditionalPythonModules='`cat $(CURDIR)/../requirements.txt | paste -s -d, -`' \
		--tags $(call params,Tags) \
		--template-file stack.yaml

destroy:
	@aws cloudformation delete-stack \
		--stack-name "$(call param,Unit)-$(call param,Environment)-$(call param,Name)-infra"

.PHONY: deploy destroy
