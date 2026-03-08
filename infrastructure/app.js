#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
require("source-map-support/register");
const cdk = __importStar(require("aws-cdk-lib"));
const ai_learning_assistant_stack_1 = require("./lib/ai-learning-assistant-stack");
const app = new cdk.App();
// Get environment configuration
const environment = app.node.tryGetContext('environment') || 'dev';
const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = process.env.CDK_DEFAULT_REGION || 'us-east-1';
// Create the main stack
new ai_learning_assistant_stack_1.AILearningAssistantStack(app, `AILearningAssistant-${environment}`, {
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiYXBwLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiYXBwLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUNBLHVDQUFxQztBQUNyQyxpREFBbUM7QUFDbkMsbUZBQTZFO0FBRTdFLE1BQU0sR0FBRyxHQUFHLElBQUksR0FBRyxDQUFDLEdBQUcsRUFBRSxDQUFDO0FBRTFCLGdDQUFnQztBQUNoQyxNQUFNLFdBQVcsR0FBRyxHQUFHLENBQUMsSUFBSSxDQUFDLGFBQWEsQ0FBQyxhQUFhLENBQUMsSUFBSSxLQUFLLENBQUM7QUFDbkUsTUFBTSxPQUFPLEdBQUcsT0FBTyxDQUFDLEdBQUcsQ0FBQyxtQkFBbUIsQ0FBQztBQUNoRCxNQUFNLE1BQU0sR0FBRyxPQUFPLENBQUMsR0FBRyxDQUFDLGtCQUFrQixJQUFJLFdBQVcsQ0FBQztBQUU3RCx3QkFBd0I7QUFDeEIsSUFBSSxzREFBd0IsQ0FBQyxHQUFHLEVBQUUsdUJBQXVCLFdBQVcsRUFBRSxFQUFFO0lBQ3RFLEdBQUcsRUFBRTtRQUNILE9BQU8sRUFBRSxPQUFPO1FBQ2hCLE1BQU0sRUFBRSxNQUFNO0tBQ2Y7SUFDRCxXQUFXLEVBQUUsV0FBVztJQUN4QixXQUFXLEVBQUUsOEVBQThFO0lBQzNGLElBQUksRUFBRTtRQUNKLE9BQU8sRUFBRSxxQkFBcUI7UUFDOUIsV0FBVyxFQUFFLFdBQVc7UUFDeEIsU0FBUyxFQUFFLEtBQUs7S0FDakI7Q0FDRixDQUFDLENBQUM7QUFFSCxHQUFHLENBQUMsS0FBSyxFQUFFLENBQUMiLCJzb3VyY2VzQ29udGVudCI6WyIjIS91c3IvYmluL2VudiBub2RlXHJcbmltcG9ydCAnc291cmNlLW1hcC1zdXBwb3J0L3JlZ2lzdGVyJztcclxuaW1wb3J0ICogYXMgY2RrIGZyb20gJ2F3cy1jZGstbGliJztcclxuaW1wb3J0IHsgQUlMZWFybmluZ0Fzc2lzdGFudFN0YWNrIH0gZnJvbSAnLi9saWIvYWktbGVhcm5pbmctYXNzaXN0YW50LXN0YWNrJztcclxuXHJcbmNvbnN0IGFwcCA9IG5ldyBjZGsuQXBwKCk7XHJcblxyXG4vLyBHZXQgZW52aXJvbm1lbnQgY29uZmlndXJhdGlvblxyXG5jb25zdCBlbnZpcm9ubWVudCA9IGFwcC5ub2RlLnRyeUdldENvbnRleHQoJ2Vudmlyb25tZW50JykgfHwgJ2Rldic7XHJcbmNvbnN0IGFjY291bnQgPSBwcm9jZXNzLmVudi5DREtfREVGQVVMVF9BQ0NPVU5UO1xyXG5jb25zdCByZWdpb24gPSBwcm9jZXNzLmVudi5DREtfREVGQVVMVF9SRUdJT04gfHwgJ3VzLWVhc3QtMSc7XHJcblxyXG4vLyBDcmVhdGUgdGhlIG1haW4gc3RhY2tcclxubmV3IEFJTGVhcm5pbmdBc3Npc3RhbnRTdGFjayhhcHAsIGBBSUxlYXJuaW5nQXNzaXN0YW50LSR7ZW52aXJvbm1lbnR9YCwge1xyXG4gIGVudjoge1xyXG4gICAgYWNjb3VudDogYWNjb3VudCxcclxuICAgIHJlZ2lvbjogcmVnaW9uLFxyXG4gIH0sXHJcbiAgZW52aXJvbm1lbnQ6IGVudmlyb25tZW50LFxyXG4gIGRlc2NyaXB0aW9uOiAnQUkgTGVhcm5pbmcgQXNzaXN0YW50IC0gU2VydmVybGVzcyBsZWFybmluZyBwbGF0Zm9ybSB3aXRoIEFXUyBBSS9NTCBzZXJ2aWNlcycsXHJcbiAgdGFnczoge1xyXG4gICAgUHJvamVjdDogJ0FJTGVhcm5pbmdBc3Npc3RhbnQnLFxyXG4gICAgRW52aXJvbm1lbnQ6IGVudmlyb25tZW50LFxyXG4gICAgTWFuYWdlZEJ5OiAnQ0RLJyxcclxuICB9LFxyXG59KTtcclxuXHJcbmFwcC5zeW50aCgpO1xyXG4iXX0=