import aws_cdk as cdk
import yaml


def synth(cls, *args, **kwargs):
    """
    Synthesize the CDK stack and return the template as a YAML string.

    :param cls: Stack class
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
        *args,
        synthesizer=cdk.DefaultStackSynthesizer(
            generate_bootstrap_version_rule=False,
        ),
        **kwargs
    )

    synthesized = app.synth()
    template = synthesized.get_stack_by_name('Stack').template
    return yaml.dump(template, sort_keys=False)

