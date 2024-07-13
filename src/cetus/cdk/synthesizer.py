import importlib

import aws_cdk as cdk
import yaml
from pyxis.config import Config, ConfigFactory


def synth(cls, config: Config, *args, **kwargs):
    """
    Synthesize the CDK stack and return the template as a YAML string.

    :param cls: Stack class
    :param config: Configuration object
    :return: Synthesized template as YAML
    """

    app = cdk.App(
        analytics_reporting=False,
        context={
            'aws:cdk:enable-path-metadata': True
        },
        outdir='cdk.out'
    )

    cls(
        app,
        'Stack',
        config,
        *args,
        synthesizer=cdk.DefaultStackSynthesizer(
            generate_bootstrap_version_rule=False,
            file_assets_bucket_name=config.file_assets_bucket_name,
            bucket_prefix=f'{config.name}/{config.env}/{config.args.stack}/{config.args.build}/'
        ),
        **kwargs
    )

    synthesized = app.synth()
    template = synthesized.get_stack_by_name('Stack').template
    return yaml.dump(template, sort_keys=False)


def main():
    """
    Entry point for CDK synthesizer.
    """

    config = ConfigFactory.default_load()
    stack_module = importlib.import_module(f'cetus.cdk.{config.args.stack}')
    stack = getattr(stack_module, f'{config.args.stack.capitalize()}Stack')
    stack_yaml = synth(stack, config)
    print(stack_yaml)


if __name__ == '__main__':
    main()
