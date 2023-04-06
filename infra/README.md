# Welcome to your CDK TypeScript project

This is a blank project for CDK development with TypeScript.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

* `npm install -g aws-cdk`  install cdk
* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template

## exec lambda pricing analysis

### unit conversions
`Amount of memory allocated: 1536 MB x 0.0009765625 GB in a MB = 1.5 GB` \
`Amount of ephemeral storage allocated: 512 MB x 0.0009765625 GB in a MB = 0.5 GB`


### pricing calculations
`4,320 requests x 60,000 ms x 0.001 ms to sec conversion factor = 259,200.00 total compute (seconds)`\
`1.50 GB x 259,200.00 seconds = 388,800.00 total compute (GB-s)`\
`388,800.00 GB-s - 400000 free tier GB-s = -11,200.00 GB-s`\
`Max (-11200.00 GB-s, 0 ) = 0.00 total billable GB-s`\
`Tiered price for: 0.00 GB-s`\
`Total tier cost = 0.0000 USD (monthly compute charges)`\
`4,320 requests - 1000000 free tier requests = -995,680 monthly billable requests`\
`Max (-995680 monthly billable requests, 0 ) = 0.00 total monthly billable requests`\
`0.50 GB - 0.5 GB (no additional charge) = 0.00 GB billable ephemeral storage per function`\

#### Lambda costs - With Free Tier (monthly): 0.00 USD


## rsi optimization lambda pricing analysis

### pricing calculations

### unit conversions
`Amount of memory allocated: 1536 MB x 0.0009765625 GB in a MB = 1.5 GB`\
`Amount of ephemeral storage allocated: 512 MB x 0.0009765625 GB in a MB = 0.5 GB`

### pricing calculations
`30 requests x 360,000 ms x 0.001 ms to sec conversion factor = 10,800.00 total compute (seconds)\
`1.50 GB x 10,800.00 seconds = 16,200.00 total compute (GB-s)`\
`16,200.00 GB-s - 400000 free tier GB-s = -383,800.00 GB-s`\
`Max (-383800.00 GB-s, 0 ) = 0.00 total billable GB-s`\
`Tiered price for: 0.00 GB-s`\
`Total tier cost = 0.0000 USD (monthly compute charges)`\
`30 requests - 1000000 free tier requests = -999,970 monthly billable requests`\
`Max (-999970 monthly billable requests, 0 ) = 0.00 total monthly billable requests`\
`0.50 GB - 0.5 GB (no additional charge) = 0.00 GB billable ephemeral storage per function`\

#### Lambda costs - With Free Tier (monthly): 0.00 USD
