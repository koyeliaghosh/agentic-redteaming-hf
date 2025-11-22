"""
ExecutorAgent: Executes adversarial prompts against target systems.
Handles request execution, retries, and error handling.
"""

import time
import logging
from typing import List, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models.data_models import AdversarialPrompt, ExecutionResult
from config import Config

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Agent responsible for executing adversarial prompts against target systems.
    Handles HTTP requests, timeouts, retries, and error handling.
    """
    
    def __init__(self, config: Config):
        """
        Initialize ExecutorAgent with configuration.
        
        Args:
            config: Application configuration containing timeout and retry settings
        """
        self.config = config
        self.timeout = config.executor_timeout_seconds
        self.delay = config.executor_delay_seconds
        self.max_retries = config.max_retries
        
        # Create session with retry configuration for network errors
        self.session = self._create_session()
        
        logger.info(
            f"ExecutorAgent initialized (timeout={self.timeout}s, "
            f"delay={self.delay}s, max_retries={self.max_retries})"
        )
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration for network errors.
        
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        # Configure retry strategy for network-level errors only
        # We handle HTTP errors and timeouts manually
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["POST", "GET"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def execute_prompt(
        self,
        prompt: AdversarialPrompt,
        target_url: str
    ) -> ExecutionResult:
        """
        Execute a single adversarial prompt against the target system.
        
        Requirement 5.1: Send each adversarial prompt to the Target_System and 
        capture the complete response.
        
        Requirement 5.2: Record execution metadata including timestamp, prompt_id, 
        response_length, and execution_time_ms.
        
        Requirement 5.3: Enforce a timeout of 30 seconds per prompt execution.
        
        Args:
            prompt: AdversarialPrompt to execute
            target_url: URL of the target system
            
        Returns:
            ExecutionResult containing response and metadata
        """
        start_time = time.time()
        timestamp = datetime.utcnow()
        
        logger.info(
            f"Executing prompt {prompt.prompt_id} "
            f"(type={prompt.attack_type}) against {target_url}"
        )
        
        try:
            # Make request with retry logic
            response = self._make_request_with_retry(
                prompt.prompt_text,
                target_url,
                attempt=0
            )
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create successful result
            result = ExecutionResult(
                prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
                response_text=response.text,
                status_code=response.status_code,
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                error=None
            )
            
            logger.info(
                f"Prompt {prompt.prompt_id} executed successfully "
                f"(status={response.status_code}, time={execution_time_ms}ms, "
                f"response_length={len(response.text)})"
            )
            
            return result
            
        except requests.exceptions.Timeout:
            # Requirement 5.4: Mark timed-out executions as failed
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Request timed out after {self.timeout}s"
            
            logger.warning(f"Prompt {prompt.prompt_id} timed out: {error_msg}")
            
            return ExecutionResult(
                prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
                response_text="",
                status_code=0,
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                error=error_msg
            )
            
        except requests.exceptions.RequestException as e:
            # Handle network errors
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Network error: {str(e)}"
            
            logger.error(f"Prompt {prompt.prompt_id} failed with network error: {error_msg}")
            
            return ExecutionResult(
                prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
                response_text="",
                status_code=0,
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                error=error_msg
            )
            
        except Exception as e:
            # Handle unexpected errors
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)}"
            
            logger.error(
                f"Prompt {prompt.prompt_id} failed with unexpected error: {error_msg}",
                exc_info=True
            )
            
            return ExecutionResult(
                prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
                response_text="",
                status_code=0,
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                error=error_msg
            )
    
    def execute_batch(
        self,
        prompts: List[AdversarialPrompt],
        target_url: str
    ) -> List[ExecutionResult]:
        """
        Execute multiple adversarial prompts sequentially against the target system.
        
        Requirement 5.5: Execute prompts sequentially to avoid overwhelming the 
        Target_System.
        
        Requirement 5.4: Continue with remaining prompts even if some fail.
        
        Args:
            prompts: List of AdversarialPrompts to execute
            target_url: URL of the target system
            
        Returns:
            List of ExecutionResults for all prompts
        """
        results = []
        total_prompts = len(prompts)
        
        logger.info(
            f"Starting batch execution of {total_prompts} prompts "
            f"against {target_url}"
        )
        
        for idx, prompt in enumerate(prompts, 1):
            # Execute single prompt
            result = self.execute_prompt(prompt, target_url)
            results.append(result)
            
            # Add delay between prompts (except after the last one)
            # Requirement 5.5: Sequential execution with delay
            if idx < total_prompts:
                logger.debug(f"Waiting {self.delay}s before next prompt...")
                time.sleep(self.delay)
        
        # Log summary
        successful = sum(1 for r in results if r.error is None)
        failed = total_prompts - successful
        
        logger.info(
            f"Batch execution completed: {successful}/{total_prompts} successful, "
            f"{failed} failed"
        )
        
        return results
    
    def _make_request_with_retry(
        self,
        prompt_text: str,
        target_url: str,
        attempt: int = 0
    ) -> requests.Response:
        """
        Make HTTP request with retry logic for network errors.
        
        Handles retries for network-level errors while respecting timeout.
        HTTP errors (4xx, 5xx) are captured and returned for analysis.
        
        Args:
            prompt_text: The adversarial prompt to send
            target_url: URL of the target system
            attempt: Current retry attempt number
            
        Returns:
            Response object from the target system
            
        Raises:
            requests.exceptions.Timeout: When request times out
            requests.exceptions.RequestException: On network errors after retries
        """
        try:
            # Make POST request to target system
            # Assuming target expects JSON with a "prompt" field
            response = self.session.post(
                target_url,
                json={"prompt": prompt_text},
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "RedTeaming-Assistant/1.0"
                }
            )
            
            # Log HTTP errors but don't raise - we want to capture the response
            if response.status_code >= 400:
                logger.warning(
                    f"Target system returned HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )
            
            return response
            
        except requests.exceptions.Timeout:
            # Don't retry on timeout - just raise
            logger.warning(f"Request timed out after {self.timeout}s")
            raise
            
        except requests.exceptions.ConnectionError as e:
            # Retry on connection errors
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{str(e)}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self._make_request_with_retry(prompt_text, target_url, attempt + 1)
            else:
                logger.error(f"Connection failed after {self.max_retries} retries")
                raise
                
        except requests.exceptions.RequestException as e:
            # Other request exceptions - retry if we have attempts left
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Request error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{str(e)}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self._make_request_with_retry(prompt_text, target_url, attempt + 1)
            else:
                logger.error(f"Request failed after {self.max_retries} retries")
                raise
    
    def close(self):
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.debug("ExecutorAgent session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
