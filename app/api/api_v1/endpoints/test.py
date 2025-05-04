from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import os
from app.core.supabase import supabase

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/supabase-connection")
async def test_supabase_connection():
    """
    Test the connection to Supabase.
    """
    try:
        # Get Supabase URL and key from environment variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        # Check if environment variables are set
        env_vars = {
            "SUPABASE_URL": bool(supabase_url),
            "SUPABASE_KEY": bool(supabase_key),
            "SESSION_ID": bool(os.environ.get("SESSION_ID"))
        }

        # Try to make a simple request to Supabase
        try:
            # Try to query the google_integrations table using a direct SQL query
            query = "SELECT * FROM public.google_integrations LIMIT 10"
            result = await supabase.execute(query)

            # Check if the table exists
            table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'google_integrations'
            )
            """
            table_exists_result = await supabase.execute(table_query)

            # List all tables in the public schema
            tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
            tables_result = await supabase.execute(tables_query)

            connection_successful = True

            # Return the google_integrations data in the response
            return {
                "supabase_url": supabase_url,
                "environment_variables": env_vars,
                "connection_successful": connection_successful,
                "development_mode": os.environ.get("ENVIRONMENT") == "development",
                "google_integrations": result,
                "table_exists": table_exists_result,
                "tables": tables_result
            }
        except Exception as e:
            logger.error(f"Error connecting to Supabase: {str(e)}")
            connection_successful = False

        return {
            "supabase_url": supabase_url,
            "environment_variables": env_vars,
            "connection_successful": connection_successful,
            "development_mode": os.environ.get("ENVIRONMENT") == "development"
        }
    except Exception as e:
        logger.error(f"Error testing Supabase connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing Supabase connection: {str(e)}")

@router.post("/create-test-table")
async def create_test_table():
    """
    Create a test table in Supabase.
    """
    try:
        # Create a test table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.test_calendar_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title TEXT NOT NULL,
            description TEXT,
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE NOT NULL,
            user_id UUID NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
        await supabase.execute(create_table_query)

        # Insert a test record
        insert_query = """
        INSERT INTO public.test_calendar_events (
            title, description, start_time, end_time, user_id
        ) VALUES (
            'Test Event', 'This is a test event', NOW(), NOW() + INTERVAL '1 hour', '00000000-0000-0000-0000-000000000000'
        ) RETURNING *
        """
        result = await supabase.execute(insert_query)

        return {
            "success": True,
            "message": "Test table created and test record inserted",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error creating test table: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating test table: {str(e)}")

@router.get("/test-calendar-events")
async def get_test_calendar_events():
    """
    Get all test calendar events.
    """
    try:
        # Query the test_calendar_events table
        query = "SELECT * FROM public.test_calendar_events"
        result = await supabase.execute(query)

        return {
            "success": True,
            "events": result
        }
    except Exception as e:
        logger.error(f"Error getting test calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting test calendar events: {str(e)}")

@router.get("/list-tables")
async def list_tables():
    """
    List all tables in the database.
    """
    try:
        # List all tables in the public schema
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        result = await supabase.execute(query)

        # Check if specific tables exist
        google_integrations_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'google_integrations'
        )
        """
        google_integrations_exists = await supabase.execute(google_integrations_query)

        test_calendar_events_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'test_calendar_events'
        )
        """
        test_calendar_events_exists = await supabase.execute(test_calendar_events_query)

        return {
            "success": True,
            "tables": result,
            "google_integrations_exists": google_integrations_exists,
            "test_calendar_events_exists": test_calendar_events_exists
        }
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing tables: {str(e)}")
