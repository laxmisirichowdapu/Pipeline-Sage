import os
from hindsight_client import Hindsight

class HindsightMemory:
    def __init__(self):
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "pipelinesage")
        self.client = Hindsight(
            base_url=os.getenv(
                "HINDSIGHT_BASE_URL",
                "https://api.hindsight.vectorize.io",
            ),
            api_key=os.getenv("HINDSIGHT_API_KEY"),
        )

    def retain_incident(self, incident):
        content = f"""
DevOps pipeline incident.

Deployment: #{incident['deployment_id']}
Date: {incident.get('date', 'unknown')}
Service: {incident['service']}
Branch: {incident['branch']}
Environment: {incident['environment']}
Commit: {incident['commit']}
Status: {incident['status']}

Failure:
{incident['error']}

Root cause:
{incident.get('root_cause', 'Not yet confirmed.')}

Infrastructure change:
{incident.get('infrastructure_change', 'None recorded.')}

Resolution:
{incident.get('resolution', 'Not yet resolved.')}

Outcome:
{incident.get('outcome', 'No outcome recorded.')}

Source incident:
Deployment #{incident['deployment_id']}

Related historical incident:
{incident.get(
    'related_historical_incident',
    'Not specified.'
)}
"""
        return self.client.retain(
            bank_id=self.bank_id,
            content=content.strip(),
        )

    def recall(self, query, limit=5):
        result = self.client.recall(
            bank_id=self.bank_id,
            query=query,
            max_tokens=4096,
            budget="mid",
        )

        memories = []
        for item in getattr(result, "results", []) or []:
            text = getattr(item, "text", None)
            if text:
                memories.append(text)
        return memories[:limit]
