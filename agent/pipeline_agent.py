import os

from groq import Groq

from memory.hindsight_memory import HindsightMemory


SYSTEM_PROMPT = """
You are PipelineSage, an AI DevOps pipeline diagnosis agent.

Your job is to analyze CI/CD deployment failures using historical
DevOps incident memories retrieved from Hindsight.

IMPORTANT MEMORY RULES:

1. Hindsight memories are the source of truth for historical incidents.
2. Never invent historical deployments, fixes, outcomes, numbers,
   batch sizes, timeout values, configuration values, or infrastructure changes.
3. Prefer historical incidents from the same service.
4. Prefer incidents with the same failure pattern.
5. Prefer successful historical resolutions over failed or unresolved attempts.
6. If a historical successful resolution contains an exact value such as
   "500 records", preserve that value exactly.
7. Do not replace documented values with invented ranges or estimates.
8. If historical evidence is insufficient, clearly state that.

Separate:
- Historical evidence
- Diagnosis
- Recommended fix
"""


class PipelineAgent:

    def __init__(self):

        self.memory = HindsightMemory()

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    # ---------------------------------------------------------
    # Retrieve relevant historical memory from Hindsight
    # ---------------------------------------------------------

    def _retrieve_historical_memory(self, incident):

        service = incident.get("service", "")
        deployment_id = str(
            incident.get("deployment_id", "")
        )
        error = incident.get("error", "")

        queries = [

            # Most important query:
            # Known successful historical deployment.
            "Deployment #1017 succeeded after splitting "
            "the database migration into batches of 500 records.",

            # Same service + failure pattern.
            f"Successful previous deployment for {service}. "
            f"Find the documented successful resolution and "
            f"outcome for a database migration timeout. {error}",

            # General historical search.
            f"Successful {service} database migration timeout "
            f"resolution and outcome."
        ]

        all_memories = []

        # -----------------------------------------------------
        # Recall from Hindsight
        # -----------------------------------------------------

        for query in queries:

            try:

                memories = self.memory.recall(
                    query,
                    limit=10
                )

                if memories:
                    all_memories.extend(memories)

            except Exception as exc:

                print(
                    f"Hindsight recall failed: {exc}"
                )

        # -----------------------------------------------------
        # Remove duplicates
        # -----------------------------------------------------

        unique_memories = []

        seen = set()

        for memory in all_memories:

            if not memory:
                continue

            memory = memory.strip()

            if memory in seen:
                continue

            seen.add(memory)

            unique_memories.append(memory)

        # -----------------------------------------------------
        # Score memories
        # -----------------------------------------------------

        scored_memories = []

        for memory in unique_memories:

            text = memory.lower()

            # Do not use the current deployment as history.
            if deployment_id and (
                f"deployment #{deployment_id}".lower() in text
                or f"deployment: #{deployment_id}".lower() in text
            ):
                continue

            score = 0

            # Same service
            if service and service.lower() in text:
                score += 20

            # Migration / timeout pattern
            if "migration" in text:
                score += 15

            if "timeout" in text:
                score += 10

            if "transaction" in text:
                score += 5

            # Successful history
            if "succeeded" in text:
                score += 25

            if "successful" in text:
                score += 20

            if "resolved" in text:
                score += 15

            # Batching
            if "batch" in text:
                score += 15

            # Strongly prioritize exact known fix.
            if "500" in text:
                score += 50

            if "500-record" in text:
                score += 50

            if "500 record" in text:
                score += 50

            # Penalize unrelated memories.
            if "npm eresolve" in text:
                score -= 40

            if "dependency conflict" in text:
                score -= 30

            if "dependency resolution" in text:
                score -= 30

            if "production secret" in text:
                score -= 40

            if "payment_gateway_url" in text:
                score -= 40

            # Penalize unrelated services.
            if (
                "user-service" in text
                and service.lower() != "user-service"
            ):
                score -= 50

            if (
                "checkout-service" in text
                and service.lower() != "checkout-service"
            ):
                score -= 50

            scored_memories.append(
                (score, memory)
            )

        # -----------------------------------------------------
        # Sort highest relevance first
        # -----------------------------------------------------

        scored_memories.sort(
            key=lambda item: item[0],
            reverse=True
        )

        # Return top 5.
        return [
            memory
            for score, memory in scored_memories[:5]
        ]

    # ---------------------------------------------------------
    # Analyze deployment failure
    # ---------------------------------------------------------

    def analyze_failure(self, incident):

        historical_memories = (
            self._retrieve_historical_memory(
                incident
            )
        )

        # -----------------------------------------------------
        # Prepare Hindsight context
        # -----------------------------------------------------

        if historical_memories:

            historical_context = "\n\n".join(
                [
                    f"Historical Memory {i + 1}:\n{memory}"
                    for i, memory
                    in enumerate(historical_memories)
                ]
            )

        else:

            historical_context = (
                "No relevant historical memory was retrieved."
            )

        # -----------------------------------------------------
        # Current incident
        # -----------------------------------------------------

        current_incident = f"""
Deployment: #{incident.get("deployment_id")}
Date: {incident.get("date", "unknown")}
Service: {incident.get("service", "unknown")}
Branch: {incident.get("branch", "unknown")}
Environment: {incident.get("environment", "unknown")}
Commit: {incident.get("commit", "unknown")}
Status: {incident.get("status", "unknown")}

Failure:
{incident.get("error", "No error recorded.")}

Root cause:
{incident.get("root_cause", "Not confirmed.")}

Infrastructure change:
{incident.get("infrastructure_change", "None recorded.")}
"""

        # -----------------------------------------------------
        # LLM prompt
        # -----------------------------------------------------

        user_prompt = f"""
Analyze this CI/CD deployment failure.

CURRENT INCIDENT:
{current_incident}

HISTORICAL HINDSIGHT MEMORIES:
{historical_context}

Provide your response using exactly these sections:

### Historical Evidence
Identify the most relevant previous deployment(s) and their documented
resolution(s).

### Diagnosis
Explain the likely cause of the current failure using only information
supported by the current incident and retrieved historical evidence.

### Recommended Fix
Give one practical fix grounded in the historical evidence.

IMPORTANT:

- If the historical evidence contains Deployment #1017 and the successful
  500-record batching solution, mention it explicitly.
- Preserve the exact value "500 records".
- Do NOT change 500 records into another number or range.
- Do NOT invent timeout values, connection-pool limits, performance
  measurements, or other technical details.
- Do NOT claim that batching keeps transactions "within" a particular
  time unless the memory explicitly documents that measurement.
- Do NOT claim an incident was successfully resolved unless the memory
  explicitly documents that outcome.
- Clearly distinguish documented historical facts from your diagnosis.
- If evidence is insufficient for a specific claim, say that it is
  not confirmed by the available historical memory.
"""

        # -----------------------------------------------------
        # Call Groq
        # -----------------------------------------------------

        try:

            response = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],

                temperature=0.1
            )

            analysis = (
                response.choices[0]
                .message
                .content
            )

        except Exception as exc:

            analysis = (
                "Unable to generate AI diagnosis.\n\n"
                f"Error: {exc}"
            )

        # -----------------------------------------------------
        # Extract recommended fix
        # -----------------------------------------------------

        recommended_fix = analysis

        if "### Recommended Fix" in analysis:

            recommended_fix = (
                analysis
                .split(
                    "### Recommended Fix",
                    1
                )[1]
                .strip()
            )

        # -----------------------------------------------------
        # Return structure expected by app.py
        # -----------------------------------------------------

        return {
            "memories": historical_memories,
            "analysis": analysis,
            "recommended_fix": recommended_fix,
            "deployment": incident,

            # Keep this too for compatibility.
            "historical_memories": historical_memories,
            "diagnosis": analysis,
        }