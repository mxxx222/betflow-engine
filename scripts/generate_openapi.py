#!/usr/bin/env python3
"""
Generate OpenAPI specification for BetFlow Engine API.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.main import app

def generate_openapi_spec():
    """Generate OpenAPI specification."""
    openapi_spec = app.openapi()
    
    # Add legal compliance information
    openapi_spec["info"]["x-legal-mode"] = "analytics-only"
    openapi_spec["info"]["x-compliance"] = "educational-only"
    openapi_spec["info"]["x-restrictions"] = [
        "No betting facilitation",
        "No fund movement",
        "No tips or recommendations",
        "Analytics data only"
    ]
    
    # Add security information
    openapi_spec["security"] = [
        {
            "BearerAuth": []
        }
    ]
    
    openapi_spec["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key"
        }
    }
    
    # Add compliance headers to all endpoints
    for path, methods in openapi_spec["paths"].items():
        for method, details in methods.items():
            if isinstance(details, dict) and "responses" in details:
                for status_code, response in details["responses"].items():
                    if "headers" not in response:
                        response["headers"] = {}
                    response["headers"]["X-Legal-Mode"] = {
                        "description": "Legal compliance mode",
                        "schema": {
                            "type": "string",
                            "enum": ["analytics-only"]
                        }
                    }
                    response["headers"]["X-Compliance"] = {
                        "description": "Compliance status",
                        "schema": {
                            "type": "string",
                            "enum": ["educational-only"]
                        }
                    }
    
    return openapi_spec

def save_openapi_spec(spec, filename="openapi.json"):
    """Save OpenAPI specification to file."""
    filepath = Path("docs") / filename
    filepath.parent.mkdir(exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(spec, f, indent=2)
    
    print(f"OpenAPI specification saved to {filepath}")

def main():
    """Main function."""
    print("Generating OpenAPI specification...")
    
    spec = generate_openapi_spec()
    save_openapi_spec(spec)
    
    print("OpenAPI specification generated successfully!")
    print(f"API Title: {spec['info']['title']}")
    print(f"API Version: {spec['info']['version']}")
    print(f"Total Endpoints: {len(spec['paths'])}")

if __name__ == "__main__":
    main()
