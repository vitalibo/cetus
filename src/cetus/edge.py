class LambdaEdge:
    """
    LambdaEdge is an interface for updating code on AWS Lambda.
    """

    def update_code(self, metadata: dict) -> None:
        pass
