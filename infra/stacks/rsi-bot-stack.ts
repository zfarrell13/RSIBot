import { Stack, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { Function, Runtime, Code } from 'aws-cdk-lib/aws-lambda';

interface RsiBotStackProps extends StackProps {
  bucketName: string;
}
export class RsiBotStack extends Stack {
  public readonly bucket: Bucket;

  constructor(scope: Construct, id: string, props: RsiBotStackProps) {
    super(scope, id, props);

    this.bucket = this._createS3Bucket(props.bucketName);
    this._createRsiOptimizationsLambda();
  }

  _createS3Bucket(bucketName: string): Bucket {
    const s3Bucket = new Bucket(this, 'rsi-bot-bucket', {
      bucketName,
      removalPolicy: RemovalPolicy.RETAIN,
    });

    return s3Bucket;
  }

  _createRsiOptimizationsLambda(): void {
    const rsiOptimizationsFunction = new Function(
      this,
      'rsi-optimizations-function',
      {
        runtime: Runtime.PYTHON_3_9,
        handler: 'rsi_optimizations.lambda_handler',
        code: Code.fromAsset('lambdas'),
        memorySize: 256,
        timeout: Duration.minutes(10),
      }
    );
  }
}

