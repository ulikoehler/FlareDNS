#!/usr/bin/env python3
import time
import argparse
import sys
import structlog
import CloudFlare
import requests

logger = structlog.get_logger()

def check_and_perform_ipv4_update(cf, hostname):
    a_record = cf.zones.dns_records.get(zone_id, params={"name": hostname, "type": "A"})[0]

    try:
        current_ipv4 = requests.get("https://api4.ipify.org").text
    except requests.exceptions.ConnectionError as ex:
        logger.error("Failed to find our IPv4 address", exception=str(ex))
        return

    # Check if we need to update
    need_to_update_a_record = a_record["content"] != current_ipv4

    # Update A record
    if need_to_update_a_record:
        old_ip = a_record["content"]
        a_record["content"] = current_ipv4
        cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
        logger.info(f"Updated IPv4 DNS record", old=old_ip, new=current_ipv4, hostname=hostname)

def check_and_perform_ipv6_update(cf, hostname):
    aaaa_record = cf.zones.dns_records.get(zone_id, params={"name": hostname, "type": "AAAA"})[0]

    try:
        current_ipv6 = requests.get("https://api6.ipify.org").text
    except requests.exceptions.ConnectionError as ex:
        logger.error("Failed to find our IPv6 address", exception=str(ex))
        current_ipv6 = None

    # Check if we need to update
    need_to_update_aaaa_record = (aaaa_record["content"] != current_ipv6) and current_ipv6 is not None

    # Update AAAA record
    if need_to_update_aaaa_record:
        old_ip = aaaa_record["content"]
        aaaa_record["content"] = current_ipv6
        cf.zones.dns_records.put(zone_id, aaaa_record["id"], data=aaaa_record)
        logger.info(f"Updated IPv6 DNS record", old=old_ip, new=current_ipv6, hostname=hostname)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--email", required=True, help="The Cloudflare login email to use")
    parser.add_argument("-k", "--api-key", required=True, help="The Cloudflare global API key to use. NOTE: Domain-specific API tokens will NOT work!")
    parser.add_argument("-n", "--hostname", required=True, help="The hostname to update, e.g. mydyndns.mydomain.com")
    parser.add_argument("-4", "--ipv4", action="store_true", help="Update A record with the current IPv4")
    parser.add_argument("-6", "--ipv6", action="store_true", help="Update AAAA record with the current IPv6")
    parser.add_argument("-i", "--interval", type=int, default=60, help="The update interval in seconds. Set to 0 to only update once. Strictly speaking the sleep time after any update attempt")
    args = parser.parse_args()
                        
    if not args.ipv4 and not args.ipv6:
        logger.error("Please use at least one of --ipv4 and --ipv6")
        sys.exit(1)

    # Extract domain from hostname: "test.mydomain.com" => mydomain.com
    domain = ".".join(args.hostname.split(".")[-2:])

    # Initialize Cloudflare API client
    cf = CloudFlare.CloudFlare(
        email=args.email,
        token=args.api_key
    )
    # Get zone ID. This is done only once and it's assumed to not chage
    zones = cf.zones.get(params={"name": domain})
    if len(zones) == 0:
        logger.error("Could not find any zones for domain, please check --hostname", domain=domain, hostname=args.hostname)
        sys.exit(2)
    zone_id = zones[0]["id"]
    # Update loop
    while True:
        if args.ipv4:
            check_and_perform_ipv4_update(cf, args.hostname)
        if args.ipv6:
            check_and_perform_ipv6_update(cf, args.hostname)
        # Check for "only update once" option
        if args.interval == 0:
            break
        time.sleep(args.interval)
    