import { parse } from 'yaml';
import { readFileSync } from 'fs';
import { join } from 'path';

const configFilePath = join(__dirname, 'config.yaml');

const readConfigFile = readFileSync(configFilePath, 'utf8');

const config = parse(readConfigFile);

export const stackName = config.stackName;

export const env = {
  region: config.env.region,
  account: config.env.account,
};

const bucketName = config.s3Bucket.name;

export const rsiBotStackProps = {
  env,
  bucketName,
};

