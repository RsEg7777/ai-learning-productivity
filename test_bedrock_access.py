"""Test Bedrock access directly."""
import boto3
import json

def test_bedrock():
    """Test if we can invoke Bedrock."""
    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Try to invoke Nova
        body = {
            "messages": [{"role": "user", "content": "Say hello"}],
            "inferenceConfig": {
                "max_new_tokens": 50,
                "temperature": 0.7,
            }
        }
        
        print("Attempting to invoke Bedrock...")
        response = client.invoke_model(
            modelId='us.amazon.nova-pro-v1:0',
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json',
        )
        
        response_body = json.loads(response['body'].read())
        output = response_body.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        text = content[0].get('text', '') if content else ''
        
        print("✅ SUCCESS! Bedrock is working!")
        print(f"Response: {text}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's an access denied error
        if 'AccessDeniedException' in str(e):
            print("\n🔍 This is an access denied error.")
            print("You may need to:")
            print("1. Request model access in Bedrock console")
            print("2. Wait for IAM permissions to propagate (can take 5-10 minutes)")
        
        return False

if __name__ == '__main__':
    test_bedrock()
