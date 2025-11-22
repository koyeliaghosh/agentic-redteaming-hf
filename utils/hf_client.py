"""
Hugging Face API client wrapper.
Handles LLM inference and embedding generation with retry logic and error handling.
"""

import time
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HuggingFaceAPIError(Exception):
    """Base exception for Hugging Face API errors."""
    pass


class RateLimitError(HuggingFaceAPIError):
    """Raised when API rate limit is exceeded (429)."""
    pass


class ModelUnavailableError(HuggingFaceAPIError):
    """Raised when model is unavailable (503)."""
    pass


class AuthenticationError(HuggingFaceAPIError):
    """Raised when authentication fails (401)."""
    pass


class TimeoutError(HuggingFaceAPIError):
    """Raised when request times out."""
    pass


class HuggingFaceClient:
    """
    Client for interacting with Hugging Face Inference API.
    Supports LLM text generation and embedding generation with retry logic.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api-inference.huggingface.co/models",
        timeout: int = 60,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        """
        Initialize Hugging Face client.
        
        Args:
            api_key: Hugging Face API key (must start with 'hf_')
            base_url: Base URL for Hugging Face Inference API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier for retries
        """
        if not api_key or not api_key.startswith("hf_"):
            raise ValueError("Invalid API key format. Must start with 'hf_'")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Create session with retry configuration
        self.session = self._create_session()
        
        logger.info("HuggingFaceClient initialized successfully")
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration.
        
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        # Configure retry strategy for network errors only
        # We'll handle API errors (429, 503, 401) manually for better control
        retry_strategy = Retry(
            total=0,  # We handle retries manually
            backoff_factor=self.backoff_factor,
            status_forcelist=[],  # We handle status codes manually
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.
        
        Returns:
            Dictionary of headers including authorization
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        attempt: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            url: Full URL for the API endpoint
            payload: Request payload
            attempt: Current retry attempt number
            
        Returns:
            Response JSON data
            
        Raises:
            RateLimitError: When rate limit is exceeded after retries
            ModelUnavailableError: When model is unavailable after retries
            AuthenticationError: When authentication fails
            TimeoutError: When request times out
            HuggingFaceAPIError: For other API errors
        """
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            # Handle authentication errors (no retry)
            if response.status_code == 401:
                logger.error("Authentication failed - invalid API key")
                raise AuthenticationError("Invalid API key or unauthorized access")
            
            # Handle rate limiting with retry
            if response.status_code == 429:
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Rate limit exceeded (429). Retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    return self._make_request_with_retry(url, payload, attempt + 1)
                else:
                    logger.error("Rate limit exceeded after max retries")
                    raise RateLimitError("Rate limit exceeded after maximum retries")
            
            # Handle model unavailable with retry
            if response.status_code == 503:
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Model unavailable (503). Retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    return self._make_request_with_retry(url, payload, attempt + 1)
                else:
                    logger.error("Model unavailable after max retries")
                    raise ModelUnavailableError("Model unavailable after maximum retries")
            
            # Handle other HTTP errors
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                logger.error(error_msg)
                raise HuggingFaceAPIError(error_msg)
            
            # Success - return JSON response
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout}s")
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during request: {str(e)}")
            raise HuggingFaceAPIError(f"Network error: {str(e)}")
    
    def generate_text(
        self,
        model: str,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate text using a Hugging Face LLM.
        
        Args:
            model: Model identifier (e.g., 'google/flan-t5-base')
            prompt: Input prompt for text generation
            max_length: Maximum length of generated text
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text string
            
        Raises:
            HuggingFaceAPIError: On API errors
        """
        url = f"{self.base_url}/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": temperature,
                "top_p": top_p,
                **kwargs
            }
        }
        
        logger.debug(f"Generating text with model {model}")
        
        try:
            response_data = self._make_request_with_retry(url, payload)
            
            # Handle different response formats
            if isinstance(response_data, list) and len(response_data) > 0:
                if isinstance(response_data[0], dict) and "generated_text" in response_data[0]:
                    generated_text = response_data[0]["generated_text"]
                else:
                    generated_text = str(response_data[0])
            elif isinstance(response_data, dict) and "generated_text" in response_data:
                generated_text = response_data["generated_text"]
            else:
                generated_text = str(response_data)
            
            logger.debug(f"Successfully generated text ({len(generated_text)} chars)")
            return generated_text
            
        except HuggingFaceAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text generation: {str(e)}")
            raise HuggingFaceAPIError(f"Text generation failed: {str(e)}")
    
    def generate_embedding(
        self,
        model: str,
        text: str
    ) -> List[float]:
        """
        Generate embedding vector for text using a Hugging Face embedding model.
        
        Args:
            model: Embedding model identifier (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            HuggingFaceAPIError: On API errors
        """
        url = f"{self.base_url}/{model}"
        
        payload = {
            "inputs": text
        }
        
        logger.debug(f"Generating embedding with model {model}")
        
        try:
            response_data = self._make_request_with_retry(url, payload)
            
            # Handle different response formats
            if isinstance(response_data, list):
                # Direct list of floats or nested list
                if isinstance(response_data[0], (int, float)):
                    embedding = response_data
                elif isinstance(response_data[0], list):
                    embedding = response_data[0]
                else:
                    raise ValueError(f"Unexpected embedding format: {type(response_data[0])}")
            else:
                raise ValueError(f"Unexpected response format: {type(response_data)}")
            
            logger.debug(f"Successfully generated embedding (dim={len(embedding)})")
            return embedding
            
        except HuggingFaceAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during embedding generation: {str(e)}")
            raise HuggingFaceAPIError(f"Embedding generation failed: {str(e)}")
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.debug("HuggingFaceClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
