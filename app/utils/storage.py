"""
AWS S3 storage utilities
"""
import os
import io
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from PIL import Image
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Manager:
    """AWS S3 storage manager"""
    
    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.enabled = bool(self.aws_access_key and self.aws_secret_key and self.bucket_name)
        
        if self.enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
            logger.info("S3 storage enabled")
        else:
            self.s3_client = None
            logger.warning("S3 storage disabled - credentials not provided")
    
    def upload_from_url(
        self,
        image_url: str,
        key: str,
        content_type: str = 'image/jpeg'
    ) -> Optional[str]:
        """
        Download image from URL and upload to S3
        
        Args:
            image_url: URL of the image to download
            key: S3 key/path for the image
            content_type: MIME type of the image
        
        Returns:
            S3 URL of uploaded image or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            # Download image from URL
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=response.content,
                ContentType=content_type,
                Metadata={
                    'uploaded-at': datetime.utcnow().isoformat(),
                    'source-url': image_url
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            logger.info(f"Uploaded image to S3: {s3_url}")
            return s3_url
        
        except requests.RequestException as e:
            logger.error(f"Error downloading image from {image_url}: {str(e)}")
            return None
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            return None
    
    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = 'image/jpeg'
    ) -> Optional[str]:
        """
        Upload bytes directly to S3
        
        Args:
            data: File data as bytes
            key: S3 key/path
            content_type: MIME type
        
        Returns:
            S3 URL or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata={'uploaded-at': datetime.utcnow().isoformat()}
            )
            
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            logger.info(f"Uploaded bytes to S3: {s3_url}")
            return s3_url
        
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            return None
    
    def delete_object(self, key: str) -> bool:
        """Delete an object from S3"""
        if not self.enabled:
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted S3 object: {key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            return False
    
    def get_object_url(self, key: str) -> str:
        """Get S3 URL for an object"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
    
    def generate_key(self, page_id: str, filename: str) -> str:
        """Generate S3 key path for a file"""
        return f"linkedin-insights/{page_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"


# Global S3 manager instance
s3_manager = S3Manager()
