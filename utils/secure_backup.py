import base64

def normalize_file_entry(file_entry):
    if file_entry.get("type") == "plaintext":
        return {
            "type": "plaintext",
            "content": file_entry.get("content")
        }
    elif file_entry.get("type") == "base64":
        # Decode base64 back into real bytes
        decoded_bytes = base64.b64decode(file_entry.get("bytes"))
        mime_type = file_entry.get("mime_type", "application/octet-stream")
        return {
            "type": "binary",
            "content": decoded_bytes,
            "mime_type": mime_type
        }
    else:
        raise ValueError(f"Unknown file type: {file_entry.get('type')}")
