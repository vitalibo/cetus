from datetime import datetime

import boto3


class Distribution:
    """
    Class for managing CloudFront distributions.
    """

    def __init__(self, distribution_id: str) -> None:
        self._client = boto3.client('cloudfront')
        self.distribution_id = distribution_id

    def invalidate(self, *paths) -> None:
        """
        Invalidates the specified paths in the CloudFront distribution.

        :param paths: The paths to invalidate.
        :return: None
        """

        self._client.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': datetime.now().strftime('Cetus-%Y%m%d%H%M%S')
            }
        )
