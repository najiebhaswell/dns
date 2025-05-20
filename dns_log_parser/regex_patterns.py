import re

UNBOUND_PATTERN = re.compile(r'\[(\d+)\] unbound\[\d+:\d+\] info: \S+ (\S+)\. (\S+) (\S+) ?(\S+)?')
DNS_PROXY_FORWARD_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Forwarding query to upstream: (\S+)')
DNS_PROXY_SAFESEARCH_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Enforcing Safe Search for domain: (\S+)')
DNS_PROXY_BLOCK_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Blocking domain: (\S+)')