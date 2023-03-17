import { Stack, StackProps, RemovalPolicy } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Bucket } from 'aws-cdk-lib/aws-s3';

interface RsiBotStackProps extends StackProps {
  bucketName: string;
}
export class RsiBotStack extends Stack {
  public readonly bucket: Bucket;

  constructor(scope: Construct, id: string, props: RsiBotStackProps) {
    super(scope, id, props);

    this.bucket = this._createS3Bucket(props.bucketName);
  }

  _createS3Bucket(bucketName: string) {
    const s3Bucket = new Bucket(this, 'rsi-bot-bucket', {
      bucketName,
      removalPolicy: RemovalPolicy.RETAIN,
    });

    return s3Bucket;
  }
}

