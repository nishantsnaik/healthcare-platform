"""
LLM Service Module

This module handles AI-powered alert summarization using OpenAI's GPT-4o.
The LLM (Large Language Model) analyzes clinical alerts and generates:
1. A concise clinical summary
2. A recommended priority level
3. Reasoning for the priority assessment

Why use AI for alert summarization?
- Reduces cognitive load on caregivers
- Provides consistent clinical context
- Helps prioritize alerts based on clinical relevance
- Can detect patterns humans might miss

The service runs asynchronously in the background to avoid blocking API responses.

For beginners: This shows how to integrate AI/ML services into a web application
using async operations and background tasks.
"""

from app.models.alert import AlertPriority

from app.repositories.assignment import get_active_assignment
from app.repositories.alerts import fetch_alert
from app.core.websocket_manager import manager
from app.core.config import settings
from app.core.logging import get_logger

import json
import re

import os
from openai import AsyncOpenAI
from app.core.database import AsyncSessionLocal

logger = get_logger(__name__)


async def generate_llm_summary(alert_id: int):
    """
    Generate an AI-powered summary and priority assessment for an alert.
    
    This function uses OpenAI's GPT-4o model to analyze clinical alerts and
    generate a summary with priority recommendations. It runs asynchronously
    in the background after an alert is created.
    
    Process:
    1. Fetch the alert from the database
    2. Prepare the prompt with alert data
    3. Call OpenAI API asynchronously
    4. Parse the JSON response
    5. Update the alert with LLM-generated fields
    6. Send the summary to the assigned caregiver via WebSocket
    
    Args:
        alert_id: The unique identifier of the alert to summarize
        
    Note:
        This function is called as a background task, so it doesn't block
        the API response. Errors are logged but don't affect the alert creation.
    """
    # Clinical prompt for the LLM
    # This instructs GPT-4o to act as a clinical assistant
    prompt = """
                    You are an experienced registered nurse and clinical healthcare assistant responsible for reviewing patient alerts.

                    Your task is to analyze the alert information provided and generate:

                    1. **Alert Summary** – A concise, clinically relevant summary that explains what the alert is about and why it may require attention.
                    2. **Recommended Priority** – Assess the urgency of the alert and assign one of the following priorities:

                       * **Critical**: Immediate intervention required; potential risk to life or severe patient harm.
                       * **High**: Prompt clinical review needed; significant risk if delayed.
                       * **Medium**: Clinical attention required but not urgent.
                       * **Low**: Informational or routine follow-up; minimal immediate risk.

                    ### Input Alert Fields

                    The alert may contain some or all of the following fields:

                    * `patient_id` (int): Unique patient identifier
                    * `alert_type` (AlertType): Category or type of alert
                    * `priority` (AlertPriority): Existing system-assigned priority (if available)
                    * `status` (AlertStatus): Current alert status (e.g., NEW, ACKNOWLEDGED, RESOLVED)
                    * `bed` (str): Patient bed assignment
                    * `unit` (str): Hospital unit or department
                    * Additional alert details, measurements, observations, or clinical context may also be provided.

                    ### Instructions

                    * Focus on what a bedside nurse or clinical staff member needs to know.
                    * Use clear, concise clinical language.
                    * Highlight any potential patient safety concerns.
                    * If information is insufficient to determine urgency, make the best assessment based on the available data and explain your reasoning briefly.
                    * Do not invent clinical facts that are not present in the alert.
                    * Consider the alert type, patient location, status, and any supporting details when determining priority.
                    * The recommended priority may differ from the system-assigned priority if the clinical context suggests a different level of urgency.
                    * Return ONLY the JSON object. No explanation, no markdown, no code blocks.

                    ### Output Format

                    ```json
                    {
                      "summary": "Brief clinical summary of the alert.",
                      "recommended_priority": "Critical | High | Medium | Low",
                      "reasoning": "Short explanation for the assigned priority."
                    }
                    ```

                    ### Example

                    Input:

                    ```json
                    {
                      "patient_id": 12345,
                      "alert_type": "OXYGEN_SATURATION_LOW",
                      "status": "NEW",
                      "bed": "ICU-12",
                      "unit": "ICU",
                      "spo2": 84
                    }
                    ```

                    Output:

                    ```json
                    {
                      "summary": "New alert indicating oxygen saturation has fallen to 84% in an ICU patient. This may reflect acute respiratory compromise and requires immediate assessment.",
                      "recommended_priority": "Critical",
                      "reasoning": "Severely low oxygen saturation presents a risk of hypoxia and requires urgent intervention."
                    }
                    ```

                """

    # Use async database session
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting LLM summary generation", alert_id=alert_id)
            
            # Step 1: Fetch alert from database
            alert = await fetch_alert(db, alert_id)
            
            # Step 2: Prepare input data for the LLM
            alert_input = {
                "patient_id": alert.patient_id,
                "alert_type": alert.alert_type,
                "priority": alert.priority,
                "status": alert.status,
                "bed": alert.bed,
                "unit": alert.unit
            }

            # Step 3: Call OpenAI API asynchronously
            logger.debug("Calling OpenAI API", alert_id=alert_id, model="gpt-4o")
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nAlert data: {alert_input}"}
                ]
            )

            # Step 4: Parse the JSON response
            result = response.choices[0].message.content
            # Remove markdown code blocks if present
            result = re.sub(r'```json\n?|\n?```', '', result).strip()
            parsed = json.loads(result)

            # Step 5: Update alert with LLM-generated fields
            alert.llm_summary = parsed["summary"]
            # Convert string to enum value for consistency
            alert.llm_priority_suggestion = AlertPriority[parsed["recommended_priority"].upper()].value
            await db.commit()

            logger.info("LLM summary generated successfully", alert_id=alert_id, summary_length=len(alert.llm_summary), suggested_priority=alert.llm_priority_suggestion)

            # Step 6: Send summary to assigned caregiver via WebSocket
            assignment = get_active_assignment(alert.patient_id)
            if assignment:
                logger.debug("Sending alert via WebSocket", alert_id=alert_id, caregiver_id=assignment.caregiver_id)
                await manager.send_alert(
                    assignment.caregiver_id,
                    "default",  # device_id - would be specific in production
                    json.dumps(parsed)
                )

        except Exception as e:
            # Log errors but don't fail - alert creation should succeed even if LLM fails
            logger.error("LLM generation failed", alert_id=alert_id, error=str(e), exc_info=True)
