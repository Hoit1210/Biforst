# Troubleshooting

## 1. Gemini API returned `503 UNAVAILABLE`

### Symptom
Incident analysis could not be generated because the external model API was temporarily unavailable.

### Engineering risk
If the LLM is a hard dependency, a model outage can stop the entire response workflow.

### Resolution
The analysis function returns a reduced-fidelity fallback message when Gemini is unavailable. Operator approval and the rest of the incident workflow can continue.

### Lesson
Fallback mode preserves workflow continuity; it does not provide equivalent analytical quality.

---

## 2. Loki returned an empty or invalid response

### Symptom
Early tests produced empty response bodies or JSON parsing failures while the log pipeline was not ready.

### Resolution
The collector now checks the HTTP status and response body before parsing, catches decoding/network errors, and returns an explicit `context unavailable` value instead of failing the full Context Builder.

### Lesson
One missing telemetry source should degrade incident context, not crash the incident pipeline.

---

## 3. Discord approval links were unreliable as Markdown links

### Symptom
HTTP approval URLs containing an IP address and port were not consistently convenient to use when embedded as Markdown links.

### Resolution
The notification sends raw approve/reject URLs.

### Production follow-up
Raw query-string approval URLs are still only a prototype. Production approval should use HTTPS, authentication, signed/expiring actions, authorization, and replay protection.
