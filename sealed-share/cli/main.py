import argparse
import sys

import requests

API_URL = "http://localhost:8080"

def share(args):
    data = {
        "recipient_email": args.recipient,
        "expires_in_minutes": args.expires,
        "watermark": args.watermark,
        "filename": args.filename,
        "content": args.content
    }
    r = requests.post(f"{API_URL}/share", json=data)
    print(r.json())

def access(args):
    data = {
        "token": args.token,
        "recipient_email": args.recipient
    }
    r = requests.post(f"{API_URL}/access", json=data)
    print(r.json())

def main():
    parser = argparse.ArgumentParser(description="Sealed Share CLI")
    subparsers = parser.add_subparsers(dest="command")

    sp_share = subparsers.add_parser("share", help="Share a file/message")
    sp_share.add_argument("--recipient", required=True, help="Recipient email")
    sp_share.add_argument("--expires", type=int, default=60, help="Expires in minutes")
    sp_share.add_argument("--watermark", help="Watermark text")
    sp_share.add_argument("--filename", required=True, help="Filename")
    sp_share.add_argument("--content", required=True, help="Content (base64 or text)")
    sp_share.set_defaults(func=share)

    sp_access = subparsers.add_parser("access", help="Access a shared file/message")
    sp_access.add_argument("--token", required=True, help="Share token")
    sp_access.add_argument("--recipient", required=True, help="Recipient email")
    sp_access.set_defaults(func=access)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
