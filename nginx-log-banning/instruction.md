### Detect brute-force IPs from nginx access log `python import re import sys LOG_FILE = '/var/log/nginx/access.log' def parse_log(line): """Parse a line from nginx access log and return an IP address and URI.""" match = re.match(r'(\d+\.\d+\.\d+\.\d+) - - \[(.*?)\] ' '"(\S+) (\S+) (\S+)" (\d+) (\d+)' ' "(.*?)" "(?)"', line) if match is None: return None, None ip, _, request, _ = match.groups() uri = re.match(r'\S+/(\S+)', request).group(1) return ip, uri def detect_brute_force(log_file): """Detect brute-force attempts in nginx access log.""" ip_counts = {} for line in open(log_file): ip, uri = parse_log(line) if ip is None or uri is None: continue if uri.startswith('login.php'): ip_counts[ip] = ip_counts.get(ip, 0) + 1 for ip, count in ip_counts.items(): if count > 10: print(f'{ip} - {count} attempts') if __name__ == '__main__': if len(sys.argv) > 1: detect_brute_force(sys.argv[1]) else: detect_brute_force(LOG_FILE) ` An IP should be banned if it makes more than 5 failed POST requests ( `401` or `403` ) to `/login` or `/api/v1/auth` in any 60 second sliding window.

Requirements:

- IPv4 and IPv6 support
  ignore internal/local IPs:
  - `127.0.0.1`

- `::1`
- `10.0.0.0/8`
- `192.168.0.0/16`
- Read and edit /etc/nginx/nginx.conf
- Insert `deny <ip>;` lines in alphabetical order between:

  # BANNED_IPS_END

- `# END BANNED_IPS`

* idempotent script, no duplicate entries

- No need to restart nginx.
