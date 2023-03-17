#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { RsiBotStack } from '../stacks/rsi-bot-stack';

const app = new cdk.App();


new RsiBotStack(app, 'rsi-bot-stack', {});