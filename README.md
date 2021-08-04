# FlareDNS

FlareDNS is a Cloudflare DynDNS updater client to overcome flexibility limitations of existing clients

It gets the external IP address information from [IPify](https://www.ipify.org/) and can update both A and AAAA records simultaneously.

FlareDNS was built specifically for configurations where multiple servers share the same IPv4 address but have separate IPv6 addresses. You can easily run multiple FlareDNS instances to accomodate for multiple DNS updates.

*Note*: FlareDNS will only work when you are using the Cloudflare Nameservers for your domain. It's free and it works extremely well - I recommend it. Note the minimum TTL of 2 minutes for Cloudflare DNS (which is not really too much of a limitation in most real-world scenarios).

## Prerequisites

* You must setup your domain on Cloudflare and create the appropriate records for the (sub)domain, e.g. `dyndns.mydomain.com`
* You must create a Cloudflare global API key (domain API token currently doesn't work, pull requests welcome!)
* The system where you want to run FlareDNS must have internet access in order to request the current IP address 
* Either Python3 or Docker must be available to run FlareDNS

Install dependencies using
```sh
pip3 install -r requirements.txt
```

## How to use (without Docker)

Tell FlareDNS to check & update DNS every 60 seconds using

```sh
python update-dyndns.py --email cloudflare-email@mydomain.com --api-key c6c94fd52184dcc783c5ec1d5089ec354b9d9 --hostname dyndns.mydomain.com --ipv4 --ipv6 --interval 60
```

Command line help:
```sh
$ python update-dyndns.py --help
usage: update-dyndns.py [-h] -e EMAIL -k API_KEY -n HOSTNAME [-4] [-6] [-i INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  -e EMAIL, --email EMAIL
                        The Cloudflare login email to use
  -k API_KEY, --api-key API_KEY
                        The Cloudflare global API key to use. NOTE: Domain-specific API tokens will NOT work!
  -n HOSTNAME, --hostname HOSTNAME
                        The hostname to update, e.g. mydyndns.mydomain.com
  -4, --ipv4            Update A record with the current IPv4
  -6, --ipv6            Update AAAA record with the current IPv6
  -i INTERVAL, --interval INTERVAL
                        The update interval in seconds. Set to 0 to only update once. Strictly speaking the sleep time after any update attempt
```

## How to use (with docker)

We provide a prebuilt docker image at [Docker Hub](https://hub.docker.com/repository/docker/ulikoehler/flaredns).
This provides you with the ability to run FlareDNS in a consistent environment without having to install system-level dependencies like Python and the few libraries that FlareDNS requires

```
docker run -ti --rm --name FlareDNS-dyndns.mydomain.com ulikoehler/flaredns:latest python update-dyndns.py --email cloudflare-email@mydomain.com --api-key c6c94fd52184dcc783c5ec1d5089ec354b9d9 --hostname dyndns.mydomain.com --ipv4 --ipv6 --interval 60
```
