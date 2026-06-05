from app.models.alert import Alert, AlertPriority
from app.repositories.alerts import alerts_db
from app.repositories.assignment import get_active_assignment  # you'll stub this
from app.core.websocket_manager import manager

import json
import re

import os
from openai import AsyncOpenAI

async def generate_llm_summary(alert_id: int):
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

    try:
            alert = alerts_db.get(alert_id)
            alert_input = {

                "patient_id" : alert.patient_id,
                "alert_type": alert.alert_type,
                "priority": alert.priority,
                "status": alert.status,
                "bed": alert.bed,
                "unit": alert.unit
            }

            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nAlert data: {alert_input}"}
                ]
            )

            result = response.choices[0].message.content
            result = re.sub(r'```json\n?|\n?```', '', result).strip()
            parsed = json.loads(result)

            alert.llm_summary = parsed["summary"]
            alert.llm_priority_suggestion = AlertPriority[parsed["recommended_priority"].upper()]

            assignment = get_active_assignment(alert.patient_id)
            if assignment:
                await manager.send_alert(
                    assignment.caregiver_id,
                    "default",  # device_id — stub for now
                    json.dumps(parsed)
                )



    except Exception as e:
         print(f"LLM generation failed for alert {alert_id}: {e}")





# 1. fetch alert from alerts_db


# 2. build prompt — use your prompt design above
#    include: alert_type, priority, bed, unit, patient_id

# 3. call Anthropic API

# 4. update alert.llm_summary with response

# 5. get caregiver_id from assignment lookup (stub it for now)
#    assignment = get_active_assignment(alert.patient_id)

# 6. push updated alert via manager.send_alert()