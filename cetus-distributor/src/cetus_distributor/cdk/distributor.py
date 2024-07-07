import os.path

from aws_cdk import (
    aws_s3, aws_glue,
    aws_s3_assets,
    Stack, RemovalPolicy, Duration, aws_iam
)
from pyxis.config import Config

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), *(('..',) * 2)))


class DistributorStack(Stack):

    def __init__(self, scope, id, config: Config, **kwargs):
        super().__init__(scope, id, **kwargs)

        s3_bucket = aws_s3.Bucket(
            self, 'Bucket',
            removal_policy=RemovalPolicy.RETAIN,
            bucket_name=f'{config.name}-{config.env}-cdn-origin',
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                aws_s3.LifecycleRule(expiration=Duration.days(30))
            ],
            versioned=False
        )

        role = aws_iam.Role(
            self, 'Role',
            role_name=f'{config.name}-{config.env}-distributor-role',
            assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'),
            inline_policies={
                'Runtime': aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                's3:PutObject'
                            ],
                            resources=[
                                f'{s3_bucket.bucket_arn}/*'
                            ]
                        )
                    ]
                )
            }
        )

        glue_job = aws_glue.CfnJob(
            self, 'Job',
            role=role.role_arn,
            glue_version='4.0',
            name=f'{config.name}-{config.env}-distributor',
            command=aws_glue.CfnJob.JobCommandProperty(
                name='glueetl',
                python_version='3',
                script_location=aws_s3_assets.Asset(
                    self, 'DriverAsset',
                    path=os.path.join(ROOT_DIR, 'cetus_distributor', 'driver.py')
                ).s3_object_url
            ),
            worker_type='G.1X',
            number_of_workers=config.get('distributor.number_of_workers', 2),
            max_retries=config.get('distributor.max_retries', 0),
            timeout=config.get('distributor.timeout', 60),
            non_overridable_arguments={
                '--env': config.env,
                '--additional-python-modules': '',
                '--extra-py-files': '',
                '--distributor.bucket': s3_bucket.bucket_name,
            }
        )
