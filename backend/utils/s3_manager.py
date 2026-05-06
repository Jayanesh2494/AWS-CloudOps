import boto3
import json
import os
import uuid
from datetime import datetime, timezone
from utils.logger import get_logger
from utils.aws_helpers import get_account_id

logger = get_logger("s3_manager")

class S3Manager:
    def __init__(self, data_file="s3_buckets.json"):
        # Put the json tracking file in the backend directory
        self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", data_file)
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Ensure the tracking file exists."""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def _read_buckets(self):
        """Read tracking file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading S3 tracking file: {e}")
            return []

    def _write_buckets(self, buckets):
        """Write to tracking file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(buckets, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing S3 tracking file: {e}")

    def create_bucket(self, session, aws_session_id, is_public=False):
        """
        Create a new secure S3 bucket. If is_public is True, enables public read access for website hosting.
        """
        try:
            account_id = get_account_id(session)
            if not account_id:
                # Fallback if somehow account ID can't be fetched
                sts_client = session.client('sts')
                account_id = sts_client.get_caller_identity()['Account']

            short_uuid = uuid.uuid4().hex[:6]
            bucket_name = f"chatops-{account_id}-{short_uuid}"
            
            # 1. Create Bucket
            s3_client = session.client('s3', region_name='ap-south-1')
            
            logger.info(f"Creating bucket: {bucket_name}")
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': 'ap-south-1'
                }
            )
            
            # 2. Access Block Configuration
            if not is_public:
                logger.info(f"Blocking public access for: {bucket_name}")
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
            else:
                logger.info(f"Allowing public access for website hosting: {bucket_name}")
                # For public buckets, we still want to block ACLs but allow public bucket policies
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )
                
                # Attach public read policy
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicReadGetObject",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(policy)
                )
            
            # 3. Enable Versioning
            logger.info(f"Enabling versioning for: {bucket_name}")
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={
                    'Status': 'Enabled'
                }
            )
            
            # 4. Enable Encryption
            logger.info(f"Enabling encryption for: {bucket_name}")
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            # 5. Store Metadata
            buckets = self._read_buckets()
            bucket_record = {
                "bucket_name": bucket_name,
                "created_by": "chatbot",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "account_id": account_id,
                "session_id": aws_session_id
            }
            buckets.append(bucket_record)
            self._write_buckets(buckets)
            
            return True, bucket_name, None
        
        except Exception as e:
            error_msg = f"Failed to create bucket: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def list_buckets(self, account_mode="OUR", account_id=None):
        """
        List buckets created by chatbot. 
        Filters by account_id for USER mode, shows all (local) for OUR mode.
        """
        buckets = self._read_buckets()
        
        if account_mode == "USER" and account_id:
             return [b for b in buckets if b.get('account_id') == account_id]
        
        # Default behavior: return all tracked buckets
        return buckets

    def delete_bucket(self, bucket_name, session, account_mode="OUR", account_id=None):
        """
        Safely delete an S3 bucket and its versions.
        """
        try:
            # Validate ownership
            buckets = self._read_buckets()
            bucket_record = next((b for b in buckets if b["bucket_name"] == bucket_name), None)
            
            if not bucket_record:
                return False, f"Bucket '{bucket_name}' not found or not created by chatbot."
            
            if account_mode == "USER" and account_id and bucket_record.get('account_id') != account_id:
                  return False, f"Bucket '{bucket_name}' belongs to a different account."

            logger.info(f"Deleting bucket and all versions: {bucket_name}")
            s3_client = session.client('s3', region_name='ap-south-1')
            s3_resource = session.resource('s3', region_name='ap-south-1')
            bucket = s3_resource.Bucket(bucket_name)
            
            # Delete all versions and delete markers
            try:
                bucket.object_versions.delete()
            except Exception as e:
                 logger.warning(f"Error during version deletion (bucket may be empty or partially deleted): {e}")
                 
            # Delete any remaining objects (if versioning was off, though it shouldn't be)
            try:
                bucket.objects.all().delete()
            except Exception as e:
                 pass

            # Delete the bucket itself
            s3_client.delete_bucket(Bucket=bucket_name)
            
            # Remove from metadata
            buckets = [b for b in buckets if b["bucket_name"] != bucket_name]
            self._write_buckets(buckets)
            
            return True, f"Bucket {bucket_name} deleted successfully."
            
        except Exception as e:
            error_msg = f"Failed to delete bucket: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
    def upload_placeholder_file(self, bucket_name, session):
        """
        Uploads an initial dummy file to demonstrate functionality.
        """
        try:
             s3_client = session.client('s3', region_name='ap-south-1')
             content = b"Bucket Created Successfully\nFile Uploaded Successfully"
             s3_client.put_object(
                 Bucket=bucket_name,
                 Key="welcome.txt",
                 Body=content,
                 ContentType="text/plain"
             )
             return True
        except Exception as e:
            logger.warning(f"Failed to upload placeholder file: {e}")
            return False

    def upload_file_to_bucket(self, bucket_name, file_name, file_content, session, content_type="text/plain", is_base64=False):
        """
        Uploads a user-specified text or binary file into a bucket.
        """
        import base64
        try:
             s3_client = session.client('s3', region_name='ap-south-1')
             
             if is_base64:
                 if isinstance(file_content, str) and file_content.startswith("data:"):
                     # Strip the data url scheme prefix if it exists
                     file_content = file_content.split(",", 1)[1]
                 content_bytes = base64.b64decode(file_content)
             else:
                 # Convert content to bytes if it's a string
                 content_bytes = file_content.encode('utf-8') if isinstance(file_content, str) else file_content
             
             s3_client.put_object(
                 Bucket=bucket_name,
                 Key=file_name,
                 Body=content_bytes,
                 ContentType=content_type
             )
             logger.info(f"Uploaded {file_name} to {bucket_name}")
             return True, f"File '{file_name}' uploaded successfully to {bucket_name}."
        except Exception as e:
            error_msg = f"Failed to upload file to bucket: {e}"
            logger.error(error_msg)
            return False, error_msg
