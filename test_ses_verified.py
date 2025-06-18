#!/usr/bin/env python3

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

def test_ses_with_verified_email():
    print("🔍 Testing SES with Verified Email Address...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('.env.production')
    
    # Get configuration
    SES_REGION = os.getenv('SES_REGION', 'us-west-2')
    SES_FROM_EMAIL = os.getenv('SES_FROM_EMAIL', 'dirk@quickstark.com')
    AWS_ACCESS_KEY_ID = os.getenv('AMAZON_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AMAZON_KEY_SECRET')
    
    print(f"✅ SES_REGION: '{SES_REGION}'")
    print(f"✅ SES_FROM_EMAIL: '{SES_FROM_EMAIL}'")
    print(f"✅ AWS_ACCESS_KEY_ID: {'Set' if AWS_ACCESS_KEY_ID else 'NOT SET'}")
    print(f"✅ AWS_SECRET_ACCESS_KEY: {'Set' if AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
    print()
    
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials not set!")
        return False
        
    try:
        # Create SES client
        print(f"🔄 Creating SES client for region: {SES_REGION}")
        ses_client = boto3.client(
            'ses',
            region_name=SES_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Check verified emails
        print("🔍 Checking verified email addresses...")
        response = ses_client.list_verified_email_addresses()
        verified_emails = response.get('VerifiedEmailAddresses', [])
        print(f"📧 Verified emails: {verified_emails}")
        
        if SES_FROM_EMAIL in verified_emails:
            print(f"✅ {SES_FROM_EMAIL} is verified!")
        else:
            print(f"⚠️  {SES_FROM_EMAIL} is NOT verified individually")
        
        # Check sending quota
        print("\n🔍 Checking SES sending quota...")
        quota_response = ses_client.get_send_quota()
        print(f"📊 Daily quota: {quota_response.get('Max24HourSend', 'N/A')}")
        print(f"📊 Sent today: {quota_response.get('SentLast24Hours', 'N/A')}")
        print(f"📊 Send rate: {quota_response.get('MaxSendRate', 'N/A')} emails/second")
        
        print("\n✅ SES configuration test completed successfully!")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ SES ClientError {error_code}: {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_ses_with_verified_email() 