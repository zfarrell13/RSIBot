#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { RsiBotStack } from '../stacks/rsi-bot-stack';
import { rsiBotStackProps, stackName } from '../config';

const app = new cdk.App();

new RsiBotStack(app, stackName, rsiBotStackProps);