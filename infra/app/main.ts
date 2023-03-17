#!/usr/bin/env node
import { App } from 'aws-cdk-lib';
import { RsiBotStack } from '../stacks/rsi-bot-stack';
import { rsiBotStackProps, stackName, env } from '../config';

const app = new App();

new RsiBotStack(app, stackName, {
  ...rsiBotStackProps,
  env,
});

