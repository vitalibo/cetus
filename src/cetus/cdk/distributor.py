import os.path

from aws_cdk import Duration, RemovalPolicy, Stack, aws_glue, aws_iam, aws_s3, aws_s3_assets
from pyxis.config import Config

DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), *(('..',) * 3)))


class DistributorStack(Stack):
    """
    Distributor stack.
    """

    def __init__(self, scope, id, config: Config, **kwargs):  # pylint: disable=redefined-builtin
        super().__init__(scope, id, **kwargs)

        bucket = aws_s3.Bucket(
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
                                f'{bucket.bucket_arn}/*'
                            ]
                        ),
                        aws_iam.PolicyStatement(
                            actions=[
                                'logs:CreateLogStream',
                                'logs:PutLogEvents'
                            ],
                            resources=[
                                f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/*'
                            ]
                        ),
                        aws_iam.PolicyStatement(
                            actions=[
                                'cloudwatch:PutMetricData'
                            ],
                            resources=[
                                '*'
                            ]
                        )
                    ]
                )
            }
        )

        job = aws_glue.CfnJob(
            self, 'Job',
            role=role.role_arn,
            glue_version='4.0',
            name=f'{config.name}-{config.env}-distributor-job',
            command=aws_glue.CfnJob.JobCommandProperty(
                name='glueetl',
                python_version='3',
                script_location=aws_s3_assets.Asset(
                    self, 'DriverAsset',
                    path=os.path.join(DIR, 'src', 'cetus', 'driver.py'),
                    readers=[role]
                ).s3_object_url
            ),
            worker_type='G.1X',
            number_of_workers=config.get('distributor.number_of_workers', 2),
            max_retries=config.get('distributor.max_retries', 0),
            timeout=config.get('distributor.timeout', 60),
            non_overridable_arguments={
                '--env': config.env,
                '--additional-python-modules': ','.join(self.requirements()),
                '--extra-py-files': ','.join(self.dist()),
                '--s3-bucket': bucket.bucket_name,
                '--config-file': aws_s3_assets.Asset(
                    self, 'ConfigAsset',
                    path=os.path.join(DIR, 'application.yaml'),
                ).s3_object_url
            }
        )

        aws_glue.CfnTrigger(
            self, 'Trigger',
            name=f'{config.name}-{config.env}-distributor-trigger',
            type='SCHEDULED',
            schedule=f'cron({config.distributor.cron})',
            start_on_creation=True,
            actions=[
                aws_glue.CfnTrigger.ActionProperty(job_name=job.ref)
            ]
        )

    def dist(self):
        for file in os.listdir(os.path.join(DIR, 'dist')):
            if not file.endswith('.whl'):
                continue

            yield aws_s3_assets.Asset(
                self, f'ExtraPyFiles{file}Asset',
                path=os.path.join(DIR, 'dist', file)
            ).s3_object_url

    @staticmethod
    def requirements():
        with open(os.path.join(DIR, 'requirements.txt'), 'r', encoding='utf-8') as f:
            return f.read().splitlines()
