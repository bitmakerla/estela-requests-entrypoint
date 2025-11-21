import json
import logging
import os
import sys
from typing import List, Dict, Any

logger = logging.getLogger("requests_entrypoint")


class ReportDeployHandler:
    """
    Report deployment status to Estela API and manage ECR images.

    This handler:
    1. Detects spiders in the project
    2. Promotes candidate Docker images to production in ECR
    3. Reports deployment status to Estela API
    4. Optionally cleans up candidate images
    """

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for the handler."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def run(self):
        """Main entry point for the report deploy handler."""
        logger.info("=" * 60)
        logger.info("Estela Deploy Reporter (Requests)")
        logger.info("=" * 60)

        try:
            # Parse environment configuration
            config = self.parse_environment()
            logger.info(f"Deploy: {config['project_id']}.{config['deploy_id']}")

            # Get spiders from the project
            spiders = self.get_project_spiders()

            if spiders:
                logger.info(f"✓ Found {len(spiders)} spiders: {', '.join(spiders)}")
                status = 'SUCCESS'
                exit_code = 0
            else:
                logger.warning("✗ No spiders found in project")
                status = 'FAILURE'
                exit_code = 1

            # Handle image promotion/cleanup based on status
            cleanup_enabled = os.getenv('CLEANUP_CANDIDATE_IMAGES', 'false').lower() == 'true'

            if status == 'SUCCESS':
                # Promote candidate → production
                if not self.promote_candidate_to_production(config):
                    logger.error("Failed to promote candidate image to production")
                    status = 'FAILURE'
                    exit_code = 1
                else:
                    # Optionally clean up candidate image after successful promotion
                    if cleanup_enabled:
                        self.cleanup_candidate_image(config)
                    else:
                        logger.info("Keeping candidate image for debugging (CLEANUP_CANDIDATE_IMAGES=false)")
            else:
                # Optionally clean up candidate image on failure to save storage
                if cleanup_enabled:
                    self.cleanup_candidate_image(config)
                else:
                    logger.info("Keeping failed candidate image for debugging (CLEANUP_CANDIDATE_IMAGES=false)")

            # Update deploy status via API
            success = self.update_deploy_status(config, status, spiders)

            if not success:
                logger.error("Failed to update deploy status in API")
                exit_code = 1

            logger.info("=" * 60)
            if exit_code == 0:
                logger.info("✓ Deploy reporting completed successfully")
            else:
                logger.error("✗ Deploy reporting failed")
            logger.info("=" * 60)

            sys.exit(exit_code)

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)

            # Try to report failure
            try:
                config = self.parse_environment()
                self.update_deploy_status(config, 'FAILURE', [])
            except:
                pass

            sys.exit(1)

    def get_project_spiders(self) -> List[str]:
        """
        Get list of spiders from the requests project.
        Uses the same helper as describe_project.
        """
        try:
            from requests_entrypoint.spider_file_helpers import get_spider_names
            return get_spider_names(os.getcwd())
        except Exception as e:
            logger.error(f"Error detecting spiders: {e}")
            return []

    def parse_environment(self) -> Dict[str, Any]:
        """
        Parse environment variables for API communication.
        """
        # Parse KEY (format: "project_id.deploy_id")
        key = os.getenv('KEY', '')
        if not key or '.' not in key:
            raise ValueError("Invalid KEY environment variable. Expected format: 'project_id.deploy_id'")

        pid, did = key.split('.', 1)

        # Parse JOB_INFO
        from requests_entrypoint.utils import decode_job
        job_info = decode_job() or {}

        if not job_info:
            # Fallback to manual parsing if decode_job returns None
            job_info_str = os.getenv('JOB_INFO', '{}')
            try:
                job_info = json.loads(job_info_str)
            except json.JSONDecodeError:
                logger.error(f"Invalid JOB_INFO JSON: {job_info_str}")
                job_info = {}

        if not job_info.get('api_host'):
            raise ValueError("JOB_INFO must contain 'api_host'")

        token = os.getenv('TOKEN', '')
        if not token:
            raise ValueError("TOKEN environment variable must be set")

        return {
            'project_id': pid,
            'deploy_id': did,
            'token': token,
            'api_host': job_info['api_host'],
        }

    def promote_candidate_to_production(self, config: Dict[str, Any]) -> bool:
        """
        Promote candidate image to production using boto3.
        Retags estela_{pid}_candidate to estela_{pid}.
        """
        try:
            import boto3
            from botocore.exceptions import ClientError

            project_id = config['project_id']
            repository_name = os.getenv('REPOSITORY_NAME', 'estela')

            candidate_tag = f"estela_{project_id}_candidate"
            production_tag = f"estela_{project_id}"

            logger.info(f"Promoting {candidate_tag} → {production_tag} in repository {repository_name}")

            ecr_client = boto3.client('ecr')

            # Get candidate image manifest
            response = ecr_client.batch_get_image(
                repositoryName=repository_name,
                imageIds=[{'imageTag': candidate_tag}]
            )

            if not response.get('images'):
                logger.error(f"Candidate image not found: {candidate_tag} in repository {repository_name}")
                return False

            manifest = response['images'][0]['imageManifest']

            # Put image with production tag
            ecr_client.put_image(
                repositoryName=repository_name,
                imageManifest=manifest,
                imageTag=production_tag
            )

            logger.info(f"✓ Image promoted to production: {production_tag}")
            return True

        except ImportError:
            logger.error("boto3 not installed. Please add boto3 to requirements.txt")
            return False
        except Exception as e:
            error_code = getattr(getattr(e, 'response', {}), 'Error', {}).get('Code', '')
            if error_code == 'RepositoryNotFoundException':
                logger.error(f"ECR repository not found: {repository_name}")
            elif error_code == 'ImageNotFoundException':
                logger.error(f"Image not found: {candidate_tag}")
            else:
                logger.error(f"AWS ECR error: {e}")
            return False

    def cleanup_candidate_image(self, config: Dict[str, Any]) -> bool:
        """
        Delete candidate image to save storage costs using boto3.
        """
        try:
            import boto3
            from botocore.exceptions import ClientError

            project_id = config['project_id']
            repository_name = os.getenv('REPOSITORY_NAME', 'estela')
            candidate_tag = f"estela_{project_id}_candidate"

            logger.info(f"Cleaning up candidate image: {candidate_tag}")

            ecr_client = boto3.client('ecr')

            response = ecr_client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=[{'imageTag': candidate_tag}]
            )

            if response.get('imageIds'):
                logger.info(f"✓ Candidate image cleaned up: {candidate_tag}")
                return True
            else:
                logger.warning(f"No candidate image found to clean up: {candidate_tag}")
                return False

        except ImportError:
            logger.warning("boto3 not installed. Skipping cleanup.")
            return False
        except Exception as e:
            # Don't fail the deploy if cleanup fails
            logger.warning(f"Failed to delete candidate image: {e}")
            return False

    def update_deploy_status(self, config: Dict[str, Any], status: str, spiders: List[str]) -> bool:
        """
        Update deploy status via Estela API.

        Args:
            config: Environment configuration
            status: "SUCCESS" or "FAILURE"
            spiders: List of spider names

        Returns:
            True if update successful, False otherwise
        """
        try:
            import requests
        except ImportError:
            logger.error("requests library not installed. It should be in requirements.txt")
            return False

        url = f"{config['api_host']}/api/projects/{config['project_id']}/deploys/{config['deploy_id']}"

        headers = {
            'Authorization': f"Token {config['token']}",
            'Content-Type': 'application/json'
        }

        payload = {
            'status': status,
            'spiders_names': spiders
        }

        logger.info(f"Updating deploy status: PUT {url}")
        logger.debug(f"Payload: {payload}")

        try:
            response = requests.put(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            logger.info(f"✓ Deploy status updated successfully (HTTP {response.status_code})")
            return True

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error updating deploy status: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response body: {e.response.text}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to API: {e}")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout updating deploy status: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return False
