import re

def parse_template(body: str, contact_data: dict) -> str:
    """
    Replaces placeholders like {{name}} or {{phone_number}} with actual data from contact_data.
    """
    def replace(match):
        key = match.group(1).strip()
        return str(contact_data.get(key, match.group(0)))
    
    # Matches {{ key }}
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    return re.sub(pattern, replace, body)
