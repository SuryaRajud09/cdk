#!/usr/bin/env python3
import aws_cdk as cdk
from my_ecs_app.my_ecs_app_stack import MyNewCdkAppStack

app = cdk.App()
MyNewCdkAppStack(app, "MyNewCdkAppStack")

app.synth()

