import time

from aws_cdk import RemovalPolicy, Stack, aws_cloudfront, aws_cloudfront_origins, aws_iam, aws_lambda, aws_s3
from pyxis.resources import resource_as_str


class InterceptorStack(Stack):
    """
    Interceptor stack.
    """

    def __init__(self, scope, id, config, **kwargs):  # pylint: disable=redefined-builtin
        super().__init__(scope, id, **kwargs)

        role = aws_iam.Role(
            self, 'Role',
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal('lambda.amazonaws.com'),
                aws_iam.ServicePrincipal('edgelambda.amazonaws.com')
            ),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSServiceRoleForLambdaReplicator'),
            ],
            inline_policies={
                'Runtime': aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                's3:GetObject',
                            ],
                            resources=[
                                f'arn:aws:s3:::{config.name}-{config.env}-cdn-origin/*'
                            ]
                        )
                    ]
                )
            }
        )

        lambda_edge = aws_lambda.Function(
            self, 'Lambda',
            function_name=f'{config.name}-{config.env}-interceptor',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            role=role,
            handler='index.handler',
            code=aws_lambda.Code.from_inline(self.code(config))
        )

        lambda_edge_version = aws_lambda.Version(
            self, f'LambdaVersion{int(time.time())}',
            removal_policy=RemovalPolicy.RETAIN,
            lambda_=lambda_edge
        )

        aws_cloudfront.Distribution(
            self, 'CloudFront',
            comment='Cetus API Gateway',
            default_behavior=aws_cloudfront.BehaviorOptions(
                allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cache_policy=aws_cloudfront.CachePolicy.CACHING_OPTIMIZED,
                edge_lambdas=[
                    aws_cloudfront.EdgeLambda(
                        event_type=aws_cloudfront.LambdaEdgeEventType.ORIGIN_REQUEST,
                        function_version=lambda_edge_version
                    )
                ],
                origin=aws_cloudfront_origins.S3Origin(
                    aws_s3.Bucket.from_bucket_name(
                        self, 'Bucket', f'{config.name}-{config.env}-cdn-origin'))
            ),
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_ALL
        )

    @staticmethod
    def code(config):
        return resource_as_str(__file__, '../lambda.py') \
            .replace('{{ metadata }}', config.get('interceptor.metadata', '{}')) \
            .replace('{{ bucket }}', f'{config.name}-{config.env}-cdn-origin')
