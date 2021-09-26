#!/usr/bin/env python3
import time
import argparse
import sys
import structlog
import logging
import CloudFlare
import requests
from requests.adapters import HTTPAdapter

logger = structlog.get_logger()

def get_current_ipv4():
    try:
        return requests.get("https://api4.ipify.org", timeout=5).text
    except requests.exceptions.ConnectionError as ex:
        logger.error("Failed to find our IPv4 address", exception=str(ex))
        return None

def get_current_ipv6():
    try:
        return requests.get("https://api6.ipify.org", timeout=5).text
    except requests.exceptions.ConnectionError as ex:
        logger.error("Failed to find our IPv6 address", exception=str(ex))
        return None


def check_and_perform_ipv4_update(cf, hostname, zone_id, current_ipv4):
    a_record = cf.zones.dns_records.get(zone_id, params={"name": hostname, "type": "A"})[0]

    # Check if we need to update
    need_to_update_a_record = a_record["content"] != current_ipv4

    # Update A record
    if need_to_update_a_record:
        old_ip = a_record["content"]
        a_record["content"] = current_ipv4
        cf.zones.dns_records.put(zone_id, a_record["id"], data=a_record)
        logger.info("Updated IPv4 DNS record", old=old_ip, new=current_ipv4, hostname=hostname)
    else:
        logger.debug("IPv4 record already up-to-date", ip=current_ipv4, hostname=hostname)

def check_and_perform_ipv6_update(cf, hostname, zone_id, current_ipv6):
    aaaa_record = cf.zones.dns_records.get(zone_id, params={"name": hostname, "type": "AAAA"})[0]

    # Check if we need to update
    need_to_update_aaaa_record = aaaa_record["content"] != current_ipv6

    # Update AAAA record
    if need_to_update_aaaa_record:
        old_ip = aaaa_record["content"]
        aaaa_record["content"] = current_ipv6
        cf.zones.dns_records.put(zone_id, aaaa_record["id"], data=aaaa_record)
        logger.info("Updated IPv6 DNS record", old=old_ip, new=current_ipv6, hostname=hostname)
    else:
        logger.debug("IPv6 record already up-to-date", ip=current_ipv6, hostname=hostname)

DEFAULT_TIMEOUT = 5 # seconds

class TimeoutHTTPAdapter(HTTPAdapter):
    """Original source: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/"""
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--email", required=True, help="The Cloudflare login email to use")
    parser.add_argument("-k", "--api-key", required=True, help="The Cloudflare global API key to use. NOTE: Domain-specific API tokens will NOT work!")
    parser.add_argument("-n", "--hostname", required=True, help="The hostname to update, e.g. mydyndns.mydomain.com")
    parser.add_argument("-4", "--ipv4", action="store_true", help="Update A record with the current IPv4")
    parser.add_argument("-6", "--ipv6", action="store_true", help="Update AAAA record with the current IPv6")
    parser.add_argument("-d", "--debug", action="store_true", help="Additional debug logging")
    parser.add_argument("-i", "--interval", type=int, default=60, help="The update interval in seconds. Set to 0 to only update once. Strictly speaking the sleep time after any update attempt")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

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
    # Force set timeout for Cloudflare requests (so the request doesn't stall during reconnect events)
    cf._base.network.session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=2.5)
    cf._base.network.session.mount("https://", adapter)
    cf._base.network.session.mount("http://", adapter)
    # Get zone ID. This is done only once and it's assumed to not chage
    zones = cf.zones.get(params={"name": domain})
    if len(zones) == 0:
        logger.error("Could not find any zones for domain, please check --hostname", domain=domain, hostname=args.hostname)
        sys.exit(2)
    zone_id = zones[0]["id"]
    # Update loop
    while True:
        # Update hostname DNS with current IPv4 record
        if args.ipv4:
            try:
                current_ipv4 = get_current_ipv4()
                logger.debug("Current IPv4 address is", ip=current_ipv4)
                if current_ipv4 is not None:
                    check_and_perform_ipv4_update(cf, args.hostname, zone_id, current_ipv4)
            except Exception as ex:
                logger.exception(ex)
        # Update hostname DNS with current IPv6 record
        if args.ipv6:
            try:
                current_ipv6 = get_current_ipv6()
                logger.debug("Current IPv6 address is", ip=current_ipv6)
                if current_ipv6 is not None:
                    check_and_perform_ipv6_update(cf, args.hostname, zone_id, current_ipv6)
            except Exception as ex:
                logger.exception(ex)
        # Check for "only update once" option
        if args.interval == 0:
            logger.debug("--interval is set to 0 => exiting")
            break
        logger.debug("Sleeping for", interval=args.interval)
        time.sleep(args.interval)
    
