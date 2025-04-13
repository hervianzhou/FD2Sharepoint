#!/usr/bin/env python3
"""
Freshdesk API Client for retrieving tickets and attachments
"""
import os
import json
import requests
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FreshdeskClient:
    """
    Client for interacting with the Freshdesk API
    """
    def __init__(self, domain, api_key):
        """
        Initialize the Freshdesk client
        
        Args:
            domain (str): Freshdesk domain (e.g., 'company.freshdesk.com')
            api_key (str): Freshdesk API key
        """
        self.domain = domain
        self.api_key = api_key
        self.base_url = f"https://{domain}/api/v2/"
        self.auth = (api_key, 'X')  # API key as username, X as password
        self.headers = {
            'Content-Type': 'application/json'
        }
        
    def _make_request(self, endpoint, method='GET', params=None, data=None):
        """
        Make a request to the Freshdesk API
        
        Args:
            endpoint (str): API endpoint to call
            method (str): HTTP method (GET, POST, PUT, DELETE)
            params (dict): Query parameters
            data (dict): Request body for POST/PUT requests
            
        Returns:
            dict: Response data
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method == 'GET':
                response = requests.get(url, auth=self.auth, params=params, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, auth=self.auth, params=params, json=data, headers=self.headers)
            elif method == 'PUT':
                response = requests.put(url, auth=self.auth, params=params, json=data, headers=self.headers)
            elif method == 'DELETE':
                response = requests.delete(url, auth=self.auth, params=params, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Check if response is empty
            if not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response content: {response.content}")
            raise
            
    def get_tickets(self, page=1, per_page=100, **kwargs):
        """
        Get a list of tickets
        
        Args:
            page (int): Page number
            per_page (int): Number of tickets per page (max 100)
            **kwargs: Additional filter parameters
            
        Returns:
            list: List of ticket objects
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # Ensure we don't exceed the max of 100
        }
        
        # Add any additional filter parameters
        params.update(kwargs)
        
        return self._make_request('tickets', params=params)
        
    def get_ticket(self, ticket_id):
        """
        Get a specific ticket by ID
        
        Args:
            ticket_id (int): Ticket ID
            
        Returns:
            dict: Ticket object
        """
        return self._make_request(f'tickets/{ticket_id}')
        
    def get_ticket_attachments(self, ticket_id):
        """
        Get attachments for a specific ticket
        
        Args:
            ticket_id (int): Ticket ID
            
        Returns:
            list: List of attachment objects
        """
        ticket = self.get_ticket(ticket_id)
        return ticket.get('attachments', [])
        
    def download_attachment(self, attachment_id, download_path):
        """
        Download an attachment
        
        Args:
            attachment_id (int): Attachment ID
            download_path (str): Path to save the attachment
            
        Returns:
            str: Path to the downloaded file
        """
        url = urljoin(self.base_url, f'attachments/{attachment_id}')
        
        try:
            response = requests.get(url, auth=self.auth, stream=True)
            response.raise_for_status()
            
            # Get the filename from the Content-Disposition header if available
            content_disposition = response.headers.get('Content-Disposition')
            filename = None
            
            if content_disposition:
                import re
                filename_match = re.search(r'filename="(.+?)"', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
            
            # If filename not found in header, use the attachment ID
            if not filename:
                filename = f"attachment_{attachment_id}"
                
            file_path = os.path.join(download_path, filename)
            
            # Ensure the download directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading attachment {attachment_id}: {e}")
            raise

    def get_all_tickets(self, per_page=100):
        """
        Get all tickets using pagination
        
        Args:
            per_page (int): Number of tickets per page (max 100)
            
        Returns:
            list: List of all ticket objects
        """
        all_tickets = []
        page = 1
        more_tickets = True
        
        while more_tickets:
            logger.info(f"Fetching tickets page {page}")
            tickets = self.get_tickets(page=page, per_page=per_page)
            
            if not tickets:
                more_tickets = False
            else:
                all_tickets.extend(tickets)
                
                # Check if we've reached the last page
                if len(tickets) < per_page:
                    more_tickets = False
                else:
                    page += 1
                    
        logger.info(f"Retrieved {len(all_tickets)} tickets in total")
        return all_tickets

# Example usage
if __name__ == "__main__":
    # Replace with your actual Freshdesk domain and API key
    client = FreshdeskClient("your-domain.freshdesk.com", "your-api-key")
    
    # Get all tickets
    tickets = client.get_all_tickets()
    print(f"Retrieved {len(tickets)} tickets")
    
    # Get attachments for the first ticket (if any)
    if tickets:
        first_ticket = tickets[0]
        print(f"First ticket: {first_ticket['id']} - {first_ticket['subject']}")
        
        attachments = client.get_ticket_attachments(first_ticket['id'])
        print(f"Found {len(attachments)} attachments for ticket {first_ticket['id']}")
