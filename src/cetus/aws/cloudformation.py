import logging

import boto3


class Stack:
    """
    Class for managing CloudFormation stacks.
    """

    def __init__(self, stack_name: str):
        self._client = boto3.client('cloudformation')
        self.stack_name = stack_name

    def update(self, **kwargs) -> None:
        """
        Updates a stack with new parameters values and waits for the update to complete.

        :param kwargs: The new parameters values.
        :return: None
        """

        parameters = self._client.describe_stacks(StackName=self.stack_name)["Stacks"][0]["Parameters"]
        parameters = {o["ParameterKey"]: o["ParameterValue"] for o in parameters}
        parameters.update(kwargs)

        self._client.update_stack(
            StackName=self.stack_name,
            UsePreviousTemplate=True,
            Parameters=[
                {
                    "ParameterKey": k,
                    "ParameterValue": v
                } for k, v in parameters.items()
            ],
            Capabilities=[
                "CAPABILITY_NAMED_IAM"
            ]
        )

        logging.info("Waiting for stack update to complete")
        waiter = self._client.get_waiter("stack_update_complete")
        waiter.wait(StackName=self.stack_name)
        logging.info("Successfully updated stack")
