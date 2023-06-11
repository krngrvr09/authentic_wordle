#!/usr/bin/env python3

import aws_cdk as cdk

from wordle_cdk.wordle_cdk_stack import WordleCdkStack


app = cdk.App()
WordleCdkStack(app, "wordle-cdk")

app.synth()
