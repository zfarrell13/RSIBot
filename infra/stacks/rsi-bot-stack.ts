import { Stack, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { Function, Runtime, Code, LayerVersion } from 'aws-cdk-lib/aws-lambda';
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';

interface RsiBotStackProps extends StackProps {
  bucketName: string;
}
export class RsiBotStack extends Stack {
  public readonly bucket: Bucket;
  public readonly customLayer: LayerVersion;

  constructor(scope: Construct, id: string, props: RsiBotStackProps) {
    super(scope, id, props);

    this.bucket = this._createS3Bucket(props.bucketName);
    this.customLayer = this._createCustomLayer();
    this._createRsiOptimizationsLambda(this.customLayer);
    this._createRsiOrderExecLambda(this.customLayer);
  }

  // create s3 bucket for logs
  _createS3Bucket(bucketName: string): Bucket {
    const s3Bucket = new Bucket(this, 'rsi-bot-bucket', {
      bucketName,
      removalPolicy: RemovalPolicy.RETAIN,
    });

    return s3Bucket;
  }

  // create custom layer for ta and alpaca_trade_api packages
  _createCustomLayer(): LayerVersion {
    const customLayer = new LayerVersion(this, 'rsi-bot-custom-lambda-layer', {
      layerVersionName: 'rsi-bot-custom-lambda-layer',
      code: Code.fromAsset('lambdas/layers/rsi_layer.zip'),
      compatibleRuntimes: [Runtime.PYTHON_3_9],
      description: 'RSI Bot custom layer for ta and alpaca_trade_api packages',
    });

    return customLayer;
  }

  // create rsi optimizations lambda
  _createRsiOptimizationsLambda(customLayer: LayerVersion): void {
    const rsiOptimizationsFunction = new Function(
      this,
      'rsi-optimizations-function',
      {
        functionName: 'rsi-optimizations-function',
        runtime: Runtime.PYTHON_3_9,
        handler: 'rsi_optimizations.lambda_handler',
        code: Code.fromAsset('lambdas'),
        memorySize: 256,
        timeout: Duration.minutes(10),
        layers: [customLayer],
      }
    );

    // add scheduler
    const rule = new Rule(this, 'rsi-optimizations-rule', {
      schedule: Schedule.rate(Duration.hours(24)),
    });

    rule.addTarget(new LambdaFunction(rsiOptimizationsFunction));
  }

  // create rsi order exec lambda
  _createRsiOrderExecLambda(customLayer: LayerVersion): void {
    const rsiOrderExecLambda = new Function(this, 'rsi-order-exec-function', {
      functionName: 'rsi-order-exec-function',
      runtime: Runtime.PYTHON_3_9,
      handler: 'order_exec.lambda_handler',
      code: Code.fromAsset('lambdas'),
      memorySize: 256,
      timeout: Duration.minutes(10),
      layers: [customLayer],
    });
  }
}

