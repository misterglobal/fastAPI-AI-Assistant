from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, Optional, List, Any
import logging
import uuid

from app.core.auth import get_current_user
from app.services.ai_service import AIService
from app.repositories.agent_config_repository import AgentConfigRepository
from app.repositories.organization_repository import OrganizationRepository
from app.integrations.twilio_integration import TwilioIntegration
from app.integrations.elevenlabs_integration import ElevenLabsIntegration
from app.schemas.agent_config import AgentConfigCreate, AgentConfigUpdate, AgentConfig
from app.schemas.organization import OrganizationCreate, Organization

router = APIRouter()
ai_service = AIService()
twilio = TwilioIntegration()
elevenlabs = ElevenLabsIntegration()
logger = logging.getLogger(__name__)

@router.post("/organizations", response_model=Dict[str, str])
async def create_organization(
    org_data: OrganizationCreate = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new organization.
    """
    try:
        # Set the owner ID from the authenticated user
        if not org_data.owner_id:
            org_data.owner_id = current_user.get("sub")
        
        # Create the organization
        org_id = await OrganizationRepository.create(org_data)
        
        if not org_id:
            raise HTTPException(status_code=500, detail="Failed to create organization")
            
        return {"id": org_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/organizations", response_model=List[Organization])
async def get_organizations(current_user: Dict = Depends(get_current_user)):
    """
    Get organizations for the current user.
    """
    try:
        user_id = current_user.get("sub")
        
        # Get organizations where user is owner
        organizations = await OrganizationRepository.get_by_owner(user_id)
        
        return organizations
    
    except Exception as e:
        logger.error(f"Error getting organizations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get organizations")

@router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(
    org_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific organization.
    """
    try:
        organization = await OrganizationRepository.get_by_id(org_id)
        
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        # Verify ownership
        if organization.get("owner_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized to access this organization")
            
        return organization
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get organization")

@router.post("/agents", response_model=Dict[str, str])
async def create_agent(
    agent_data: AgentConfigCreate = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new agent configuration.
    """
    try:
        # Verify organization access
        org_id = str(agent_data.organization_id)
        organization = await OrganizationRepository.get_by_id(org_id)
        
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        if organization.get("owner_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized to create agents for this organization")
        
        # Create agent configuration
        agent_id = await AgentConfigRepository.create(agent_data)
        
        if not agent_id:
            raise HTTPException(status_code=500, detail="Failed to create agent")
            
        return {"id": agent_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/agents", response_model=List[AgentConfig])
async def get_agents(
    organization_id: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get agent configurations, optionally filtered by organization.
    """
    try:
        # If organization ID is provided, verify access
        if organization_id:
            organization = await OrganizationRepository.get_by_id(organization_id)
            
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")
                
            if organization.get("owner_id") != current_user.get("sub"):
                raise HTTPException(status_code=403, detail="Not authorized to access this organization")
                
            # Get agents for this organization
            agents = await AgentConfigRepository.get_all_by_organization(organization_id)
            return agents
        
        # Otherwise, get agents for all organizations user has access to
        orgs = await OrganizationRepository.get_by_owner(current_user.get("sub"))
        
        agents = []
        for org in orgs:
            org_agents = await AgentConfigRepository.get_all_by_organization(org["id"])
            agents.extend(org_agents)
            
        return agents
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agents")

@router.get("/agents/{agent_id}", response_model=AgentConfig)
async def get_agent(
    agent_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific agent configuration.
    """
    try:
        agent = await AgentConfigRepository.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Verify organization access
        organization = await OrganizationRepository.get_by_id(agent.get("organization_id"))
        
        if not organization or organization.get("owner_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized to access this agent")
            
        return agent
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    agent_data: AgentConfigUpdate = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Update an agent configuration.
    """
    try:
        # Get agent
        agent = await AgentConfigRepository.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Verify organization access
        organization = await OrganizationRepository.get_by_id(agent.get("organization_id"))
        
        if not organization or organization.get("owner_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized to update this agent")
            
        # Update agent
        success = await AgentConfigRepository.update(agent_id, agent_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update agent")
            
        return {"message": "Agent updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent")

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete an agent configuration.
    """
    try:
        # Get agent
        agent = await AgentConfigRepository.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Verify organization access
        organization = await OrganizationRepository.get_by_id(agent.get("organization_id"))
        
        if not organization or organization.get("owner_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized to delete this agent")
            
        # Delete agent
        success = await AgentConfigRepository.delete(agent_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete agent")
            
        return {"message": "Agent deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.get("/voices")
async def get_available_voices(current_user: Dict = Depends(get_current_user)):
    """
    Get available voices from ElevenLabs.
    """
    try:
        voices = await elevenlabs.get_voices()
        
        # Format voice information for frontend
        formatted_voices = []
        for voice in voices:
            formatted_voices.append({
                "id": voice.get("voice_id"),
                "name": voice.get("name"),
                "preview_url": voice.get("preview_url"),
                "gender": voice.get("labels", {}).get("gender"),
                "accent": voice.get("labels", {}).get("accent")
            })
            
        return {"voices": formatted_voices}
    
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available voices")

@router.post("/generate-system-prompt")
async def generate_system_prompt(
    data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate a system prompt based on business type and tone.
    """
    try:
        business_type = data.get("business_type", "general business")
        tone = data.get("tone", "professional")
        
        # Generate system prompt
        system_prompt = await ai_service.generate_system_prompt(business_type, tone)
        
        return {"system_prompt": system_prompt}
    
    except Exception as e:
        logger.error(f"Error generating system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate system prompt")

@router.get("/twilio/phone-numbers")
async def get_twilio_phone_numbers(current_user: Dict = Depends(get_current_user)):
    """
    Get available Twilio phone numbers.
    """
    # This endpoint would require a more complex integration with Twilio's API
    # For now, just return the configured number if available
    return {"phone_numbers": [twilio.phone_number] if twilio.phone_number else []}