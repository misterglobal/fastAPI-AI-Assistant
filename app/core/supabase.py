import os
from typing import Dict, Any, Optional, List, Tuple
import httpx
import json
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for interacting with Supabase API."""

    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        if not self.url:
            logger.warning("SUPABASE_URL environment variable is not set. Using dummy URL for development.")
            self.url = "https://example.supabase.co"

        self.key = os.environ.get("SUPABASE_KEY")
        if not self.key:
            logger.warning("SUPABASE_KEY environment variable is not set. Using dummy key for development.")
            self.key = "dummy_key"

        self.headers = {
            "apikey": self.key,
            "Content-Type": "application/json"
        }
        self.auth_headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }

        # Set table prefixes for the application
        self.session_id = os.environ.get("SESSION_ID")
        if not self.session_id:
            logger.warning("SESSION_ID environment variable is not set. Using dummy session ID for development.")
            self.session_id = "dev"

        self.prefix = "ai_phone_assistant"

    def get_table_name(self, entity: str) -> str:
        """Generate a properly formatted table name with prefix and session ID."""
        return f"{entity}_{self.session_id}"

    async def select(self, table: str, select: str = "*", filters: Dict = None) -> List[Dict]:
        """
        Select data from a Supabase table.

        Args:
            table: Table name (without prefix)
            select: Fields to select, default "*"
            filters: Query filters

        Returns:
            List of records
        """
        table_name = self.get_table_name(table)
        url = f"{self.url}/rest/v1/{table_name}"

        params = {"select": select}

        if filters:
            # Convert filters to query parameters
            for k, v in filters.items():
                if isinstance(v, dict):
                    # Handle operators like eq, gt, lt, etc.
                    for op, val in v.items():
                        params[f"{k}.{op}"] = val
                else:
                    params[k] = f"eq.{v}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.auth_headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error selecting from {table_name}: {str(e)}")
            # In development mode, return empty list instead of raising an exception
            if os.environ.get("ENVIRONMENT") != "production":
                logger.warning(f"Returning empty list for select from {table_name} in development mode")
                return []
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def insert(self, table: str, data: Dict) -> Dict:
        """
        Insert data into a Supabase table.

        Args:
            table: Table name (without prefix)
            data: Data to insert

        Returns:
            Inserted record
        """
        table_name = self.get_table_name(table)
        url = f"{self.url}/rest/v1/{table_name}"

        headers = {**self.auth_headers, "Prefer": "return=representation"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error inserting into {table_name}: {str(e)}")
            # In development mode, return the data with a fake ID instead of raising an exception
            if os.environ.get("ENVIRONMENT") != "production":
                logger.warning(f"Returning mock data for insert into {table_name} in development mode")
                return {**data, "id": "dev_mock_id"}
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update(self, table: str, id: str, data: Dict) -> Dict:
        """
        Update data in a Supabase table.

        Args:
            table: Table name (without prefix)
            id: Record ID
            data: Data to update

        Returns:
            Updated record
        """
        table_name = self.get_table_name(table)
        url = f"{self.url}/rest/v1/{table_name}"

        headers = {**self.auth_headers, "Prefer": "return=representation"}
        params = {"id": f"eq.{id}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=headers, params=params, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error updating {table_name}: {str(e)}")
            # In development mode, return the data with the ID instead of raising an exception
            if os.environ.get("ENVIRONMENT") != "production":
                logger.warning(f"Returning mock data for update of {table_name} in development mode")
                return {**data, "id": id}
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete(self, table: str, id: str) -> bool:
        """
        Delete data from a Supabase table.

        Args:
            table: Table name (without prefix)
            id: Record ID

        Returns:
            True if successful
        """
        table_name = self.get_table_name(table)
        url = f"{self.url}/rest/v1/{table_name}"

        params = {"id": f"eq.{id}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.auth_headers, params=params)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error deleting from {table_name}: {str(e)}")
            # In development mode, return True instead of raising an exception
            if os.environ.get("ENVIRONMENT") != "production":
                logger.warning(f"Returning success for delete from {table_name} in development mode")
                return True
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def execute(self, query: str, values: Dict = None) -> Dict:
        """
        Execute custom SQL query via Supabase REST API.

        Args:
            query: SQL query
            values: Query parameters

        Returns:
            Query results
        """
        url = f"{self.url}/rest/v1/rpc/execute"

        payload = {
            "query": query,
            "params": values or {}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.auth_headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            # In development mode, return empty dict instead of raising an exception
            if os.environ.get("ENVIRONMENT") != "production":
                logger.warning(f"Returning empty result for SQL query in development mode")
                return {"result": []}
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Initialize a global Supabase client instance
supabase = SupabaseClient()