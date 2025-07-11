import boto3
import os
import uuid
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, List
import logging
from datetime import datetime
import mimetypes

class S3Service:
    """
    S3 service for handling all file storage operations in the sketch animation system.
    Handles images, audio files, videos, and other generated content.
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from environment variables."""
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        
        # Debug prints for troubleshooting
        print("DEBUG: S3Service bucket =", self.bucket_name)
        print("DEBUG: S3Service region =", self.aws_region)
        print("DEBUG: S3Service access key =", (self.aws_access_key_id or '')[:6], "...")
        
        # Set up logging (move this up before _ensure_bucket_exists)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError("AWS credentials not properly configured. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_S3_BUCKET_NAME in environment variables.")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists, create if it doesn't."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"Bucket {self.bucket_name} exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                    )
                    self.logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    self.logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                self.logger.error(f"Error accessing bucket: {e}")
                raise
    
    def upload_file(self, file_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local path to the file
            s3_key: S3 key (path) for the file
            content_type: Optional content type for the file
            
        Returns:
            S3 URL of the uploaded file
        """
        try:
            # Determine content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload file (no ACL)
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            self.logger.info(f"Uploaded {file_path} to {s3_url}")
            
            return s3_url
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to upload {file_path}: {e}")
            raise
    
    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload bytes data to S3.
        
        Args:
            data: Bytes data to upload
            s3_key: S3 key (path) for the file
            content_type: Content type for the file
            
        Returns:
            S3 URL of the uploaded file
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type
            )
            
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            self.logger.info(f"Uploaded bytes to {s3_url}")
            
            return s3_url
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to upload bytes to {s3_key}: {e}")
            raise
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to local storage.
        
        Args:
            s3_key: S3 key (path) of the file
            local_path: Local path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            self.logger.info(f"Downloaded {s3_key} to {local_path}")
            return True
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to download {s3_key}: {e}")
            return False
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 key (path) of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.logger.info(f"Deleted {s3_key} from S3")
            return True
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to delete {s3_key}: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 key (path) of the file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                self.logger.error(f"Error checking file existence: {e}")
                return False
    
    def get_file_url(self, s3_key: str) -> str:
        """
        Get the public URL of a file in S3.
        
        Args:
            s3_key: S3 key (path) of the file
            
        Returns:
            Public S3 URL of the file
        """
        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
    
    def list_files(self, prefix: str = "") -> List[Dict]:
        """
        List files in S3 with a given prefix.
        
        Args:
            prefix: S3 key prefix to filter files
            
        Returns:
            List of file information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': self.get_file_url(obj['Key'])
                    })
            
            return files
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return []
    
    # Specific methods for sketch animation system
    
    def upload_image(self, local_image_path: str, job_id: str, index: int = 0) -> str:
        """
        Upload a generated image to S3.
        
        Args:
            local_image_path: Local path to the image file
            job_id: Unique job identifier
            index: Image index in the sequence
            
        Returns:
            S3 URL of the uploaded image
        """
        filename = os.path.basename(local_image_path)
        s3_key = f"images/{job_id}/{filename}"
        return self.upload_file(local_image_path, s3_key, 'image/png')
    
    def upload_audio(self, local_audio_path: str, job_id: str, index: int = 0) -> str:
        """
        Upload a generated audio file to S3.
        
        Args:
            local_audio_path: Local path to the audio file
            job_id: Unique job identifier
            index: Audio index in the sequence
            
        Returns:
            S3 URL of the uploaded audio file
        """
        filename = os.path.basename(local_audio_path)
        s3_key = f"audio/{job_id}/{filename}"
        return self.upload_file(local_audio_path, s3_key, 'audio/mpeg')
    
    def upload_video(self, local_video_path: str, job_id: str, video_type: str = "final") -> str:
        """
        Upload a generated video to S3.
        
        Args:
            local_video_path: Local path to the video file
            job_id: Unique job identifier
            video_type: Type of video (final, intermediate, etc.)
            
        Returns:
            S3 URL of the uploaded video
        """
        filename = os.path.basename(local_video_path)
        s3_key = f"videos/{job_id}/{video_type}_{filename}"
        return self.upload_file(local_video_path, s3_key, 'video/mp4')
    
    def get_job_files(self, job_id: str) -> Dict[str, List[str]]:
        """
        Get all files associated with a specific job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Dictionary with file URLs organized by type
        """
        files = {
            'images': [],
            'audio': [],
            'videos': []
        }
        
        # Get images
        image_files = self.list_files(f"images/{job_id}/")
        files['images'] = [f['url'] for f in image_files]
        
        # Get audio files
        audio_files = self.list_files(f"audio/{job_id}/")
        files['audio'] = [f['url'] for f in audio_files]
        
        # Get videos
        video_files = self.list_files(f"videos/{job_id}/")
        files['videos'] = [f['url'] for f in video_files]
        
        return files
    
    def cleanup_job_files(self, job_id: str) -> bool:
        """
        Clean up all files associated with a specific job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # List all files for the job
            all_files = []
            for prefix in [f"images/{job_id}/", f"audio/{job_id}/", f"videos/{job_id}/"]:
                files = self.list_files(prefix)
                all_files.extend([f['key'] for f in files])
            
            # Delete all files
            if all_files:
                objects = [{'Key': key} for key in all_files]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )
                self.logger.info(f"Cleaned up {len(all_files)} files for job {job_id}")
            
            return True
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to cleanup job {job_id}: {e}")
            return False 