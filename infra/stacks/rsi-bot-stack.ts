import { Stack, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { Function, Runtime, Code, LayerVersion } from 'aws-cdk-lib/aws-lambda';
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import {
  Role,
  ServicePrincipal,
  PolicyStatement,
  Effect,
} from 'aws-cdk-lib/aws-iam';

import { config } from 'dotenv';

config();

interface RsiBotStackProps extends StackProps {
  bucketName: string;
}

export class RsiBotStack extends Stack {
  public readonly bucket: Bucket;
  public readonly customLayer: LayerVersion;
  public readonly lambdaRole: Role;
  public readonly rsiOrderExecLambda: Function;

  constructor(scope: Construct, id: string, props: RsiBotStackProps) {
    super(scope, id, props);

    this.bucket = this._createS3Bucket(props.bucketName);
    this.lambdaRole = this._createIamAccessRole();
    this._attachIamAccessPolicy(this.lambdaRole, this.bucket);
    this.customLayer = this._createCustomLayer();
    this.rsiOrderExecLambda = this._createRsiOrderExecLambda(
      this.customLayer,
      this.lambdaRole
    );
    this._createRsiOptimizationsLambda(this.customLayer, this.lambdaRole);
  }

  // create iam access role for lambda
  _createIamAccessRole(): Role {
    const role = new Role(this, 'rsi-optimizations-function-role', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      roleName: 'rsi-optimizations-function-role',
    });

    return role;
  }

  // attach iam access policy
  _attachIamAccessPolicy(role: Role, bucket: Bucket): void {
    const iamPolicy = new PolicyStatement({
      effect: Effect.ALLOW,
      actions: ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 'logs:*'],
      resources: [bucket.arnForObjects('*'), 'arn:aws:logs:*:*:*'],
    });

    role.addToPolicy(iamPolicy);
  }

  // create s3 bucket for logs
  _createS3Bucket(bucketName: string): Bucket {
    const s3Bucket = new Bucket(this, 'rsi-bot-bucket', {
      bucketName,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    return s3Bucket;
  }

  // create custom layer for ta and alpaca_trade_api packages
  _createCustomLayer(): LayerVersion {
    const customLayer = new LayerVersion(this, 'rsi-bot-custom-lambda-layer', {
      layerVersionName: 'rsi-bot-custom-lambda-layer',
      code: Code.fromAsset('lambda_layers/rsi_layer.zip'),
      compatibleRuntimes: [Runtime.PYTHON_3_9],
      description: 'RSI Bot custom layer for ta and alpaca_trade_api packages',
    });

    return customLayer;
  }

  // create numpy layer
  _createNumpyLayer(): void {
    LayerVersion.fromLayerVersionArn(
      this,
      'numpy-managed-layer',
      'arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:4'
    );
  }

  // create rsi optimizations lambda
  _createRsiOptimizationsLambda(customLayer: LayerVersion, role: Role): void {
    const rsiOptimizationsFunction = new Function(
      this,
      'rsi-optimizations-function',
      {
        functionName: 'rsi-optimizations-function',
        runtime: Runtime.PYTHON_3_9,
        handler: 'rsi_optimizations.lambda_handler',
        code: Code.fromAsset('lambdas'),
        memorySize: 1536,
        timeout: Duration.minutes(10),
        layers: [
          customLayer,
          LayerVersion.fromLayerVersionArn(
            this,
            'numpy-managed-layer',
            'arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:4'
          ),
        ],
        environment: {
          API_KEY: process.env.API_KEY || '',
          SECRET_KEY: process.env.SECRET_KEY || '',
        },
        role: role,
      }
    );

    // add scheduler
    const rule = new Rule(this, 'rsi-optimizations-rule', {
      schedule: Schedule.rate(Duration.hours(24)),
    });

    rule.addTarget(new LambdaFunction(rsiOptimizationsFunction));
  }

  // create rsi order exec lambda
  _createRsiOrderExecLambda(customLayer: LayerVersion, role: Role): Function {
    const rsiOrderExecLambda = new Function(this, 'rsi-order-exec-function', {
      functionName: 'rsi-order-exec-function',
      runtime: Runtime.PYTHON_3_9,
      handler: 'order_exec.lambda_handler',
      code: Code.fromAsset('lambdas'),
      memorySize: 1536,
      timeout: Duration.minutes(10),
      layers: [
        customLayer,
        LayerVersion.fromLayerVersionArn(
          this,
          'np-managed-layer',
          'arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39:4'
        ),
      ],
      environment: {
        API_KEY: process.env.API_KEY || '',
        SECRET_KEY: process.env.SECRET_KEY || '',
        BASE_URL: process.env.BASE_URL || '',
      },
      role: role,
    });

    // add scheduler
    const rule = new Rule(this, 'rsi-order-exec-rule', {
      schedule: Schedule.rate(Duration.minutes(10)),
    });

    rule.addTarget(new LambdaFunction(rsiOrderExecLambda));

    return rsiOrderExecLambda;
  }
}

