from __future__ import annotations

import json
import os


def load_input_schedule(file_path: str = "input_schedule.json") -> list[tuple[int, str]]:
    """ Loads and validates the input schedule from an external JSON file.
    Returns a list of (tick, token) tuples. """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file format in {file_path}: {e}")

    if not isinstance(data, dict) or "events" not in data:
        raise ValueError(
            f"Configuration root in {file_path} must be a JSON object containing an 'events' list.")

    events = data["events"]
    if not isinstance(events, list):
        raise ValueError(f"The 'events' key in {file_path} must be a list.")

    schedule: list[tuple[int, str]] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(
                f"Event at index {index} is not a valid JSON object.")
        if "tick" not in event or "token" not in event:
            raise ValueError(
                f"Event at index {index} is missing required 'tick' or 'token' key.")

        tick = event["tick"]
        token = event["token"]

        if not isinstance(tick, int) or tick < 0:
            raise ValueError(
                f"Event tick '{tick}' at index {index} must be a non-negative integer.")
        if not isinstance(token, str):
            raise ValueError(f"Event token at index {index} must be a string.")

        schedule.append((tick, token))

    return schedule
