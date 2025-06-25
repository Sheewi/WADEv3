# -*- coding: utf-8 -*-
"""
WADE Feedback Loop
Processes outcomes for learning and adaptation.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional

# Path to feedback storage
FEEDBACK_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "WADE_RUNTIME",
        "logs",
        "feedback.json",
    )
)


def _ensure_feedback_file():
    """Ensure feedback file exists."""
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)


def _load_feedback():
    """Load feedback from file."""
    _ensure_feedback_file()

    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _save_feedback(feedback):
    """Save feedback to file."""
    _ensure_feedback_file()

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback, f, indent=2)


def record_success(message: str, context: Optional[Dict[str, Any]] = None):
    """
    Record a success event in the feedback loop.

    Args:
        message: Success message
        context: Optional context for the success
    """
    feedback = _load_feedback()

    feedback_entry = {
        "type": "success",
        "message": message,
        "context": context or {},
        "timestamp": time.time(),
    }

    feedback.append(feedback_entry)
    _save_feedback(feedback)


def record_failure(message: str, context: Optional[Dict[str, Any]] = None):
    """
    Record a failure event in the feedback loop.

    Args:
        message: Failure message
        context: Optional context for the failure
    """
    feedback = _load_feedback()

    feedback_entry = {
        "type": "failure",
        "message": message,
        "context": context or {},
        "timestamp": time.time(),
    }

    feedback.append(feedback_entry)
    _save_feedback(feedback)


def record_feedback(
    feedback_type: str, message: str, context: Optional[Dict[str, Any]] = None
):
    """
    Record a generic feedback event in the feedback loop.

    Args:
        feedback_type: Type of feedback (e.g., 'success', 'failure', 'warning')
        message: Feedback message
        context: Optional context for the feedback
    """
    feedback = _load_feedback()

    feedback_entry = {
        "type": feedback_type,
        "message": message,
        "context": context or {},
        "timestamp": time.time(),
    }

    feedback.append(feedback_entry)
    _save_feedback(feedback)


def get_recent_feedback(
    limit: int = 10, feedback_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get recent feedback events.

    Args:
        limit: Maximum number of events to return
        feedback_type: Optional type filter

    Returns:
        List of feedback events
    """
    feedback = _load_feedback()

    # Filter by type if specified
    if feedback_type:
        feedback = [entry for entry in feedback if entry.get("type") == feedback_type]

    # Sort by timestamp (most recent first)
    feedback.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

    return feedback[:limit]


def get_feedback_stats() -> Dict[str, Any]:
    """
    Get statistics about feedback events.

    Returns:
        Dictionary with feedback statistics
    """
    feedback = _load_feedback()

    stats = {
        "total": len(feedback),
        "success": len([entry for entry in feedback if entry.get("type") == "success"]),
        "failure": len([entry for entry in feedback if entry.get("type") == "failure"]),
        "other": len(
            [
                entry
                for entry in feedback
                if entry.get("type") not in ["success", "failure"]
            ]
        ),
    }

    # Calculate success rate
    if stats["total"] > 0:
        stats["success_rate"] = stats["success"] / stats["total"]
    else:
        stats["success_rate"] = 0

    return stats


def clear_feedback():
    """Clear all feedback events."""
    _save_feedback([])


def analyze_feedback_patterns() -> Dict[str, Any]:
    """
    Analyze patterns in feedback events.

    Returns:
        Dictionary with pattern analysis results
    """
    feedback = _load_feedback()

    if not feedback:
        return {"patterns_found": False, "message": "No feedback events to analyze"}

    # Count occurrences of failure messages
    failure_messages = {}
    for entry in feedback:
        if entry.get("type") == "failure":
            message = entry.get("message", "")
            failure_messages[message] = failure_messages.get(message, 0) + 1

    # Find recurring failures
    recurring_failures = [
        {"message": message, "count": count}
        for message, count in failure_messages.items()
        if count > 1
    ]

    # Sort by count (most frequent first)
    recurring_failures.sort(key=lambda x: x["count"], reverse=True)

    return {
        "patterns_found": len(recurring_failures) > 0,
        "recurring_failures": recurring_failures[:5],  # Top 5 recurring failures
        "total_failures": len(
            [entry for entry in feedback if entry.get("type") == "failure"]
        ),
        "recent_success_rate": sum(
            1 for entry in feedback[-20:] if entry.get("type") == "success"
        )
        / min(20, len(feedback)),
    }
