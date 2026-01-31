#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { AILearningAssistantStack } from './lib/ai-learning-assistant-stack';

const app = new cdk.App();

// Get environment configuration
const environment = app.node.tryGetContext('environment') || 'dev';
const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = process.env.CDK_DEFAULT_REGION || 'us-east-1';

// Create the main stack
new AILearningAssistantStack(app, `AILearningAssistant-${environment}`, {
  env: {
    account: account,
    region: region,
  },
  environment: environment,
  description: 'AI Learning Assistant - Serverless learning platform with AWS AI/ML services',
  tags: {
    Project: 'AILearningAssistant',
    Environment: environment,
    ManagedBy: 'CDK',
  },
});

app.synth();
