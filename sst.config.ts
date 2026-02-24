/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app() {
    return {
      name: "fraudasaurus",
      removal: "retain",
      protect: true,
      home: "aws",
      providers: {
        aws: {
          region: "us-east-2",
        },
      },
    };
  },
  async run() {
    new sst.aws.Nextjs("Web", {
      path: "packages/web",
      domain: "fraudasaurus.ai",
    });
  },
});
