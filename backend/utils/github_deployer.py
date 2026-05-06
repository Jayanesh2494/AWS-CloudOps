import io
import json
import zipfile
import mimetypes
import requests
from utils.logger import get_logger
from utils.s3_manager import S3Manager

logger = get_logger("github_deployer")
s3_manager = S3Manager()

def deploy_static_website_from_github(github_url: str, session, session_id: str):
    """
    Downloads a public GitHub repository and hosts it on S3 as a static website.
    
    Args:
        github_url (str): The public GitHub repository URL.
        session: boto3 session.
        session_id: The conversational session ID.
        
    Returns:
        tuple: (success_boolean, result_message, website_url)
    """
    try:
        # Standardize GitHub URL to get the zipball for the main branch
        base_url = github_url.rstrip("/")
        if base_url.endswith(".git"):
            base_url = base_url[:-4]
            
        # Try finding the default branch zip (master or main)
        zip_url_main = f"{base_url}/archive/refs/heads/main.zip"
        zip_url_master = f"{base_url}/archive/refs/heads/master.zip"
        
        logger.info(f"Attempting to download repo from: {zip_url_main}")
        response = requests.get(zip_url_main, timeout=15)
        
        if response.status_code != 200:
            logger.info(f"main branch not found, trying master: {zip_url_master}")
            response = requests.get(zip_url_master, timeout=15)
            
        if response.status_code != 200:
            return False, f"Could not download repository. Ensure it is public and has a 'main' or 'master' branch. (URL checked: {github_url})", None
            
        # 1. Create Public S3 Bucket
        success, bucket_name, error_msg = s3_manager.create_bucket(session, session_id, is_public=True)
        if not success:
            return False, f"Failed to provision infrastructure: {error_msg}", None
            
        # 2. Configure Static Web Hosting
        s3_client = session.client('s3', region_name='ap-south-1')
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'ErrorDocument': {'Key': 'error.html'},
                'IndexDocument': {'Suffix': 'index.html'},
            }
        )
        
        # 3. Extract and Upload Files
        zip_content = io.BytesIO(response.content)
        uploaded_files = 0
        
        with zipfile.ZipFile(zip_content, 'r') as z:
            # The zip file contains a root directory (e.g., repo-name-main/). We need to strip this prefix.
            file_list = z.namelist()
            if not file_list:
                return False, "The repository archive is empty.", None
                
            root_dir = file_list[0].split('/')[0] + '/'
            
            for file_path in file_list:
                # Skip directories
                if file_path.endswith('/'):
                    continue
                    
                # Strip root directory prefix
                s3_key = file_path[len(root_dir):] if file_path.startswith(root_dir) else file_path
                
                # We skip hidden directories and files such as .git/ or .github/
                if s3_key.startswith('.') or '/.' in s3_key:
                    continue
                    
                file_data = z.read(file_path)
                
                # Guess MIME type
                content_type, _ = mimetypes.guess_type(s3_key)
                if not content_type:
                    if s3_key.endswith('.css'):
                        content_type = 'text/css'
                    elif s3_key.endswith('.js'):
                        content_type = 'application/javascript'
                    elif s3_key.endswith('.html'):
                        content_type = 'text/html'
                    elif s3_key.endswith('.json'):
                        content_type = 'application/json'
                    else:
                        content_type = 'application/octet-stream'
                        
                # Put object
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_data,
                    ContentType=content_type
                )
                uploaded_files += 1

        website_url = f"http://{bucket_name}.s3-website.ap-south-1.amazonaws.com"
        return True, f"Successfully deployed {uploaded_files} files.", website_url

    except Exception as e:
        logger.error(f"GitHub Static Website Deployment Failed: {str(e)}")
        return False, f"Deployment failed: {str(e)}", None
