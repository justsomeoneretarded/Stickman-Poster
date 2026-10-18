"""Explicit optional OpenAI-compatible endpoint; no paid endpoint is a default."""
import json
import os
import urllib.request

from .project import validate

SYSTEM = """Write an original, catchy animated explainer/story as JSON only.
Return schema_version:1, title, description, keywords:[strings], scenes:[objects].
Each scene: unique id, duration (seconds,1–45), location (room/street/diagram/stage),
action (idle/point/walk/float/think/worried/celebrate), heading (<=72 characters),
label (<=90 characters), narration (short paragraph), secondary (boolean),
levitate (boolean), camera_zoom (1 to 1.12).
Build a specific opening, progression and payoff. Avoid repetitive generic hooks.
Use varied shots/actions within this actual renderer vocabulary. Do not describe
unimplemented locations or pretend the renderer can draw arbitrary props.
Do not invent statistics, quotes or scientific facts. For factual topics include
only supported claims from the supplied notes; otherwise make the story explicitly
fictional. Do not copy an existing video's script. No markdown fences.
Estimate 150–170 narration words per minute, allowing pauses. Target duration is
a writing budget, not guaranteed final runtime; actual TTS determines timing.
"""


def plan(title, minutes, endpoint, model, notes=""):
    if not title.strip() or not 0.1 <= minutes <= 20:
        raise ValueError("Provide a title and target length between .1 and 20 minutes")
    if not endpoint.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        raise ValueError("Use HTTPS or a local development endpoint")
    payload = {"model": model, "messages": [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Title: {title}\nTarget: {minutes} minutes\nSource notes: {notes}"}],
               "temperature": 0.7, "max_tokens": 10000}
    headers = {"Content-Type": "application/json"}
    if os.environ.get("STUDIO_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["STUDIO_API_KEY"]
    def complete(body):
        request = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions",
                                         data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=240) as response:
            result = json.load(response)
        text = result["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text[text.find("\n")+1:text.rfind("```")]
        return validate(json.loads(text))
    draft = complete(payload)
    revision = {**payload, "messages": payload["messages"] + [
        {"role": "assistant", "content": json.dumps(draft)},
        {"role": "user", "content": "Edit this draft: strengthen the concrete opening, remove repetition and generic filler, make actions match the actual supported visuals, check internal story/prop continuity, preserve supported facts and uncertainty, improve the payoff. Return the full revised JSON only. Do not add unsupported claims to make it sound more dramatic."}]}
    return complete(revision)
