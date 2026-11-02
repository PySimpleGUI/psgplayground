"""
network_scanner_v2.pyw - LAN device scanner with a tile view modeled on the "Relay" discovery screen.

Finds every device on the local subnet and shows, per device:
    name (best of mDNS / DNS / NetBIOS / SSDP), .local mDNS name, IP, MAC + vendor, ping time,
    open service ports, mDNS service types, UPnP server string, and a guessed device kind (color coded).

Discovery methods used (standard library only besides PySimpleGUI - runs on Python 3.6 and up):
    * ICMP ping sweep of the subnet (parallel)              -> alive hosts + round-trip time
    * ARP table (arp -a)                                    -> MAC addresses, plus silent hosts
    * Reverse DNS (gethostbyaddr)                           -> router-assigned DNS names
    * mDNS reverse PTR query sent directly to each host     -> "EPSONA71835.local" style names
    * mDNS service enumeration (multicast)                  -> _ipp, _airplay, _googlecast ...
    * SSDP / UPnP M-SEARCH (multicast)                      -> SERVER strings for routers, TVs, etc.
    * NetBIOS name query (nbtstat -A, Windows only)         -> Windows computer names
    * TCP connect probe of common ports                     -> what the device offers
    * Optional online MAC vendor lookup (api.macvendors.com) -> manufacturer

Legend at the top: click a device kind to hide / show those tiles (toggles, remembered between runs).

Diagnose button: dumps ipconfig / route / ping / arp / firewall output to network_scanner_diag.txt when a scan finds nothing.

Keyboard: Up/Down = 1 row, PgUp/PgDn = 1 page, Home/End = top/bottom, F5 = rescan, Escape = close

--demo   shows a made-up home network instead of scanning yours (for screenshots, or to try it out): 192.168.1.x addresses, made-up
         names and locally administered MACs.  Your subnet setting isn't saved and the tiles' Open links are off.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v2.1  --demo: a made-up network (every kind of device) instead of a scan - nothing of yours ends up in a screenshot; version shown
"""

import PySimpleGUI as sg
import os
import socket
import struct
import subprocess
import sys
import ipaddress
import queue
import threading
import time
import re
import uuid
import webbrowser
import urllib.request
from concurrent.futures import ThreadPoolExecutor

VERSION = '2.1'
DEMO = '--demo' in sys.argv                    # made-up devices, nothing is scanned - see the top of the file
DEMO_SUBNET = '192.168.1.0/24'

# ----------------------------------------------------------------------------------------------------------------------
# Keys
# ----------------------------------------------------------------------------------------------------------------------
K_SUBNET = '-SUBNET-'
K_COLUMNS = '-COLUMNS-'
K_VENDOR = '-VENDOR-'
K_SCAN = '-SCAN-'
K_STOP = '-STOP-'
K_DIAG = '-DIAG-'
K_DIAG_DONE = '-DIAG DONE-'
K_MAIL = '-MAIL-'              # doorbell: a worker thread put a message in the mailbox
K_GRID = '-GRID-'
K_STATUS = '-STATUS-'
K_PROGRESS = '-PROGRESS-'
K_COUNT = '-COUNT-'
K_FOUND = '-FOUND-'            # thread -> GUI: one device dict
K_DONE = '-DONE-'              # thread -> GUI: scan finished
K_PHASE = '-PHASE-'            # thread -> GUI: status text + progress fraction
K_VENDOR_UPDATE = '-VENDOR UPDATE-'
K_TILE_DETAILS = '-DETAILS-'
KT_DETAILS = lambda ip: (K_TILE_DETAILS, ip)
K_TILE_OPEN = '-OPEN-'
KT_OPEN = lambda ip: (K_TILE_OPEN, ip)
K_FILTER = '-FILTER-'          # legend toggles at the top: one per device kind, click to show/hide that kind
KT_FILTER = lambda kind: (K_FILTER, kind)
K_HIDDEN_KINDS = '-HIDDEN KINDS-'   # settings entry: list of kinds currently hidden

# ----------------------------------------------------------------------------------------------------------------------
# Look - a dark palette patterned after the Relay screenshot.  Every kind gets a color AND a text label.
# ----------------------------------------------------------------------------------------------------------------------
BG = '#0f1117'            # window background
TILE_BG = '#1c1f2e'       # tile body
TILE_BORDER = '#2a2e45'
TEXT = '#e6e8f0'
MUTED = '#8a8fb5'
LINK = '#7aa2ff'

KIND_COLORS = {           # device kind -> accent color (used for the tile title and kind label)
    'This PC': '#3ddc97',
    'Gateway': '#c084fc',
    'Printer': '#ffa94d',
    'Windows PC': '#60a5fa',
    'Apple': '#f1f5f9',
    'Linux / NAS': '#fbbf24',
    'Media / TV': '#f472b6',
    'IoT / Camera': '#2dd4bf',
    'Unknown': '#9ca3af',
}

sg.theme_add_new('RelayDark', {'BACKGROUND': BG, 'TEXT': TEXT, 'INPUT': TILE_BG, 'TEXT_INPUT': TEXT, 'SCROLL': TILE_BORDER,
                               'BUTTON': (TEXT, '#2f3350'), 'PROGRESS': ('#3ddc97', TILE_BORDER), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('RelayDark')

FONT = ('Segoe UI', 10)
FONT_SMALL = ('Segoe UI', 9)
FONT_TITLE = ('Segoe UI', 11, 'bold')
FONT_HEADER = ('Segoe UI', 16, 'bold')

COMMON_PORTS = {21: 'ftp', 22: 'ssh', 23: 'telnet', 53: 'dns', 80: 'http', 135: 'rpc', 139: 'netbios', 443: 'https', 445: 'smb', 515: 'lpd', 548: 'afp',
                554: 'rtsp', 631: 'ipp', 1883: 'mqtt', 3389: 'rdp', 5000: 'upnp/synology', 5353: 'mdns', 5900: 'vnc', 7000: 'airplay', 8008: 'cast', 8080: 'http-alt',
                8443: 'https-alt', 8883: 'mqtts', 9100: 'jetdirect', 32400: 'plex', 62078: 'iphone-sync'}

CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith('win') else 0     # keeps ping/arp/nbtstat from flashing console windows under .pyw

stop_flag = threading.Event()

# ----------------------------------------------------------------------------------------------------------------------
# Thread -> GUI messaging.  The tile grid is rebuilt by replacing the whole window, so worker threads must never hold on to a window
# object (posting to a closed one raises and kills the thread).  They put messages in a mailbox that outlives windows, then ring a
# doorbell on whichever window is current.
# ----------------------------------------------------------------------------------------------------------------------
class AppWin:
    current = None            # the window on screen right now


mailbox = queue.Queue()


def post(key, value=None):
    """Worker threads call this instead of window.write_event_value.  Mail first, THEN ring - a ring that lands on a window being
    replaced is harmless because replace_window() re-rings when mail is waiting."""
    mailbox.put((key, value))
    try:
        AppWin.current.write_event_value(K_MAIL, None)
    except Exception:
        pass

# ----------------------------------------------------------------------------------------------------------------------
# Local network info
# ----------------------------------------------------------------------------------------------------------------------
def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def default_gateway():
    """Best-effort gateway detection: ipconfig on Windows, 'ip route' elsewhere.  Falls back to x.x.x.1"""
    try:
        if sys.platform.startswith('win'):
            out = run_text(['ipconfig'], 5)[1]
            m = re.search(r'Default Gateway[ .]*:\s*(\d+\.\d+\.\d+\.\d+)', out)
        else:
            out = run_text(['sh', '-c', 'ip route 2>/dev/null || route -n'], 5)[1]
            m = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', out) or re.search(r'^0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', out, re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return '.'.join(local_ip().split('.')[:3]) + '.1'


def run_text(cmd, timeout):
    """subprocess.run that also works on Python 3.6 (capture_output= and text= are 3.7+).  Returns (exit code, stdout, stderr) as text;
    odd console code-page bytes become replacement characters instead of raising."""
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    return r.returncode, r.stdout.decode(errors='replace'), r.stderr.decode(errors='replace')


def local_mac():
    n = uuid.getnode()
    return ':'.join(f'{(n >> (8 * i)) & 0xff:02X}' for i in reversed(range(6)))


# ----------------------------------------------------------------------------------------------------------------------
# Discovery primitives
# ----------------------------------------------------------------------------------------------------------------------
ping_errors = []          # exceptions raised trying to RUN ping (not "no reply") - shown in the status line so a broken ping.exe is obvious


def ping(ip):
    """Returns round-trip ms (float) if host answered, else None"""
    if sys.platform.startswith('win'):
        cmd = ['ping', '-n', '1', '-w', '700', ip]
    else:
        cmd = ['ping', '-c', '1', '-W', '1', ip]
    try:
        out = run_text(cmd, 12)[1]
    except Exception as e:
        ping_errors.append(repr(e))
        return None
    if re.search(r'ttl[=:]', out, re.I):                                  # a real echo reply (not "destination unreachable", which also exits 0 on Windows)
        m = re.search(r'(?:time|zeit|temps|tiempo)\s*[=<]\s*([\d.]+)\s*ms', out, re.I)
        return float(m.group(1)) if m else 0.0
    return None


def arp_prime(ips):
    """Ping-independent presence check: a UDP datagram to each host forces the OS to ARP for it, so hosts whose firewall drops
    ICMP echo still show up in the ARP table afterwards.  Nothing needs to answer the datagram."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(False)
    for ip in ips:
        if stop_flag.is_set():
            break
        try:
            s.sendto(b'\x00', (ip, 9))
        except Exception:
            pass
        time.sleep(0.003)                                                  # ~0.8 s for a /24, keeps the ARP cache from thrashing
    s.close()
    time.sleep(1.5)


def arp_table():
    """Returns {ip: 'AA:BB:CC:DD:EE:FF'} from the OS ARP cache"""
    table = {}
    try:
        if sys.platform.startswith('win'):
            out = run_text(['arp', '-a'], 10)[1]
        else:
            out = run_text(['sh', '-c', 'ip neigh 2>/dev/null || arp -an'], 10)[1]
    except Exception:
        return table
    for m in re.finditer(r'(\d+\.\d+\.\d+\.\d+)\D+?([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})', out):
        mac = m.group(2).replace('-', ':').upper()
        if mac not in ('FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00') and not mac.startswith('01:00:5E'):
            table[m.group(1)] = mac
    return table


def reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ''


def netbios_name(ip):
    """Windows only: nbtstat -A ip  ->  computer name (the <00> UNIQUE entry)"""
    if not sys.platform.startswith('win'):
        return ''
    try:
        out = run_text(['nbtstat', '-A', ip], 6)[1]
        m = re.search(r'^\s*(\S+)\s+<00>\s+UNIQUE', out, re.M)
        return m.group(1) if m else ''
    except Exception:
        return ''


# ---- tiny DNS packet helpers (enough for mDNS PTR queries / answers) -------------------------------------------------
def dns_encode_name(name):
    return b''.join(bytes([len(p)]) + p.encode() for p in name.strip('.').split('.')) + b'\x00'


def dns_decode_name(data, off):
    """Decode a (possibly compressed) DNS name. Returns (name, next_offset)"""
    labels, jumped, next_off, hops = [], False, 0, 0
    while True:
        if off >= len(data):
            break
        ln = data[off]
        if ln == 0:
            off += 1
            break
        if ln & 0xC0 == 0xC0:
            if not jumped:
                next_off = off + 2
            off = ((ln & 0x3F) << 8) | data[off + 1]
            jumped = True
            hops += 1
            if hops > 20:
                break
            continue
        labels.append(data[off + 1:off + 1 + ln].decode(errors='replace'))
        off += 1 + ln
    return '.'.join(labels), (next_off if jumped else off)


def dns_parse_answers(data):
    """Returns list of (name, rtype, rdata) for all answer/authority/additional records, PTR/A/TXT decoded"""
    recs = []
    try:
        qd, an, ns, ar = struct.unpack('!HHHH', data[4:12])
        off = 12
        for _ in range(qd):
            _, off = dns_decode_name(data, off)
            off += 4
        for _ in range(an + ns + ar):
            name, off = dns_decode_name(data, off)
            rtype, _, _, rdlen = struct.unpack('!HHIH', data[off:off + 10])
            off += 10
            rdata = data[off:off + rdlen]
            if rtype == 12:                                   # PTR
                target, _ = dns_decode_name(data, off)
                recs.append((name, 'PTR', target))
            elif rtype == 1 and rdlen == 4:                   # A
                recs.append((name, 'A', socket.inet_ntoa(rdata)))
            elif rtype == 16:                                 # TXT
                txt, p = [], 0
                while p < len(rdata):
                    l = rdata[p]
                    txt.append(rdata[p + 1:p + 1 + l].decode(errors='replace'))
                    p += 1 + l
                recs.append((name, 'TXT', txt))
            off += rdlen
    except Exception:
        pass
    return recs


def mdns_reverse_name(ip, timeout=1.2):
    """Ask the host directly (legacy unicast mDNS query) for its .local name via a reverse PTR lookup"""
    rev = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
    pkt = struct.pack('!HHHHHH', 0x1234, 0, 1, 0, 0, 0) + dns_encode_name(rev) + struct.pack('!HH', 12, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(pkt, (ip, 5353))
        data, _ = s.recvfrom(4096)
        s.close()
        for name, rtype, rdata in dns_parse_answers(data):
            if rtype == 'PTR':
                return rdata
    except Exception:
        pass
    return ''


def mdns_browse_services(listen_time=2.5):
    """Multicast '_services._dns-sd._udp.local' query. Returns {ip: set(service types)} keyed by the responder's source IP"""
    found = {}
    pkt = struct.pack('!HHHHHH', 0, 0, 1, 0, 0, 0) + dns_encode_name('_services._dns-sd._udp.local') + struct.pack('!HH', 12, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(0.3)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        s.sendto(pkt, ('224.0.0.251', 5353))
        end = time.time() + listen_time
        while time.time() < end:
            try:
                data, (src, _) = s.recvfrom(9000)
            except socket.timeout:
                continue
            for name, rtype, rdata in dns_parse_answers(data):
                if rtype == 'PTR' and name.startswith('_services._dns-sd'):
                    found.setdefault(src, set()).add(rdata.replace('.local', ''))
        s.close()
    except Exception:
        pass
    return found


def ssdp_search(listen_time=2.5):
    """UPnP M-SEARCH. Returns {ip: {'server': ..., 'location': ...}}"""
    found = {}
    msg = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'.encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.settimeout(0.3)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        s.sendto(msg, ('239.255.255.250', 1900))
        end = time.time() + listen_time
        while time.time() < end:
            try:
                data, (src, _) = s.recvfrom(4096)
            except socket.timeout:
                continue
            hdrs = {}
            for line in data.decode(errors='replace').split('\r\n')[1:]:
                if ':' in line:
                    k, v = line.split(':', 1)
                    hdrs[k.strip().lower()] = v.strip()
            d = found.setdefault(src, {'server': '', 'location': ''})
            d['server'] = d['server'] or hdrs.get('server', '')
            d['location'] = d['location'] or hdrs.get('location', '')
        s.close()
    except Exception:
        pass
    return found


def probe_ports(ip, timeout=0.6):
    open_ports = []
    for port in COMMON_PORTS:
        if stop_flag.is_set():
            break
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            s.close()
        except Exception:
            pass
    return open_ports


def vendor_lookup(mac):
    """Free online OUI lookup (1 request/sec limit).  Returns '' on any failure."""
    try:
        req = urllib.request.Request(f'https://api.macvendors.com/{mac}', headers={'User-Agent': 'network_scanner'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode(errors='replace').strip()[:40]
    except Exception:
        return ''


# ----------------------------------------------------------------------------------------------------------------------
# Diagnostics - everything needed to see WHY a scan found nothing.  Raw command output, no interpretation.
# ----------------------------------------------------------------------------------------------------------------------
def run_cmd(cmd, timeout=15):
    t0 = time.time()
    try:
        code, so, se = run_text(cmd, timeout)
        out = (so + se).strip()
        return f'$ {" ".join(cmd)}    (exit {code}, {time.time() - t0:.2f} s)\n{out}\n'
    except Exception as e:
        return f'$ {" ".join(cmd)}    FAILED after {time.time() - t0:.2f} s: {e!r}\n'


def diagnostics():
    my, gw = local_ip(), default_gateway()
    win = sys.platform.startswith('win')
    parts = [f'network_scanner diagnostics  {time.strftime("%Y-%m-%d %H:%M:%S")}', f'Python {sys.version.split()[0]}  on  {sys.platform}  host {socket.gethostname()}',
             f'local_ip() = {my}    default_gateway() = {gw}    local_mac() = {local_mac()}', '']
    parts.append(run_cmd(['ipconfig', '/all'] if win else ['sh', '-c', 'ip addr; ip route']))
    parts.append(run_cmd(['route', 'print', '0.0.0.0'] if win else ['sh', '-c', 'ip route show default']))
    parts.append(run_cmd(['ping', '-n', '2', '-w', '1000', gw] if win else ['ping', '-c', '2', '-W', '1', gw]))
    parts.append(run_cmd(['ping', '-n', '1', '-w', '1000', '8.8.8.8'] if win else ['ping', '-c', '1', '-W', '1', '8.8.8.8']))
    parts.append(f'ping() helper on gateway {gw} -> {ping(gw)!r}   errors: {ping_errors[-1:] or "none"}\n')
    arp_prime([gw, my])
    parts.append(run_cmd(['arp', '-a'] if win else ['sh', '-c', 'ip neigh || arp -an']))
    parts.append(f'arp_table() parsed -> {arp_table()}\n')
    parts.append(run_cmd(['netsh', 'advfirewall', 'show', 'currentprofile'] if win else ['sh', '-c', 'echo no firewall query on this OS']))
    parts.append(run_cmd(['netsh', 'interface', 'ipv4', 'show', 'interfaces'] if win else ['sh', '-c', 'echo -']))
    parts.append(f'mDNS reverse lookup of gateway -> {mdns_reverse_name(gw)!r}')
    parts.append(f'mDNS services seen -> {mdns_browse_services(1.5)}')
    parts.append(f'SSDP responders -> {list(ssdp_search(1.5))}')
    parts.append(f'TCP probe of gateway -> open ports {probe_ports(gw)}')
    return '\n'.join(parts)


# ----------------------------------------------------------------------------------------------------------------------
# Device classification
# ----------------------------------------------------------------------------------------------------------------------
def guess_kind(dev, my_ip, gateway):
    ports, services, vendor = set(dev['ports']), ' '.join(dev['services']).lower(), dev['vendor'].lower()
    names = (dev['name'] + ' ' + dev['mdns'] + ' ' + dev['upnp']).lower()
    if dev['ip'] == my_ip:
        return 'This PC'
    if dev['ip'] == gateway:
        return 'Gateway'
    if ports & {9100, 631, 515} or '_ipp' in services or '_printer' in services or any(w in names + vendor for w in ('epson', 'brother', 'canon', 'hp ', 'hewlett', 'lexmark')):
        return 'Printer'
    if '_airplay' in services or '_companion-link' in services or '_raop' in services or 62078 in ports or 'apple' in vendor or 7000 in ports:
        return 'Apple'
    if '_afpovertcp' in services or (5000 in ports and 445 in ports) or any(w in names + vendor for w in ('synology', 'qnap', 'nas', 'ubiquiti', 'unifi')):
        return 'Linux / NAS'
    if '_googlecast' in services or 8008 in ports or 32400 in ports or any(w in names + vendor for w in ('roku', 'sonos', 'samsung', 'lg ', 'vizio', 'tv', 'chromecast', 'fire')):
        return 'Media / TV'
    if ports & {3389} or (445 in ports and 135 in ports) or dev['netbios']:
        return 'Windows PC'
    if 22 in ports or '_ssh' in services or any(w in names + vendor for w in ('raspberry', 'linux', 'debian', 'ubuntu')):
        return 'Linux / NAS'
    if ports & {554, 1883, 8883} or any(w in names + vendor for w in ('espressif', 'tuya', 'ring', 'nest', 'wyze', 'amazon', 'camera', 'hikvision', 'dahua')):
        return 'IoT / Camera'
    return 'Unknown'


def best_name(dev):
    upnp = re.search(r'UPnP/[\d.]+\s+(.+)', dev['upnp'])                 # "Linux/4.9 UPnP/1.0 Chromecast/1.0" -> "Chromecast/1.0"
    for n in (dev['mdns'].replace('.local', ''), dev['netbios'], dev['dns'].split('.')[0], upnp.group(1).strip() if upnp else ''):
        if n and n != dev['ip']:
            return n
    return dev['ip']


# ----------------------------------------------------------------------------------------------------------------------
# The scan - runs in a worker thread, reports back with write_event_value
# ----------------------------------------------------------------------------------------------------------------------
def scan_thread(subnet, want_vendor):
    my_ip, gateway = local_ip(), default_gateway()
    try:
        net = ipaddress.ip_network(subnet, strict=False)
        hosts = [str(h) for h in net.hosts()] if net.num_addresses > 2 else [str(net.network_address)]
    except Exception as e:
        post(K_PHASE, (f'Bad subnet "{subnet}": {e}', 0))
        post(K_DONE, [])
        return
    if len(hosts) > 1024:
        hosts = hosts[:1024]

    # Phase 1 - ping sweep + multicast discovery (in parallel)
    ping_errors.clear()
    post(K_PHASE, (f'Pinging {len(hosts)} addresses on {net} ...', 0.05))
    alive = {}
    services, upnp = {}, {}
    disc = threading.Thread(target=lambda: (services.update(mdns_browse_services()), upnp.update(ssdp_search())), daemon=True)
    disc.start()
    with ThreadPoolExecutor(max_workers=48 if sys.platform.startswith('win') else 96) as pool:
        futures = {pool.submit(ping, ip): ip for ip in hosts}
        for i, f in enumerate(futures):
            if stop_flag.is_set():
                break
            rtt = f.result()
            if rtt is not None:
                alive[futures[f]] = rtt
            if i % 16 == 0:
                post(K_PHASE, (f'Pinging ... {i + 1}/{len(hosts)}  ({len(alive)} alive)', 0.05 + 0.45 * i / len(hosts)))
    disc.join(timeout=4)
    post(K_PHASE, (f'Ping found {len(alive)} alive.  Checking the ARP table for hosts that ignore ping ...', 0.48))
    arp_prime(hosts)
    arp = arp_table()
    if ping_errors:
        post(K_PHASE, (f'WARNING: ping could not be run ({len(ping_errors)} failures) - {ping_errors[0][:80]}.  Run Diagnose.', 0.48))
        time.sleep(2)
    for ip in list(arp) + list(services) + list(upnp):
        if ipaddress.ip_address(ip) in net and ip not in alive:
            alive[ip] = None                                          # in ARP/mDNS/SSDP but no ping reply
    if my_ip not in alive and ipaddress.ip_address(my_ip) in net:
        alive[my_ip] = 0.0
    ips = sorted(alive, key=lambda s: ipaddress.ip_address(s))

    # Phase 2 - per-host identification
    post(K_PHASE, (f'Identifying {len(ips)} devices ...', 0.5))

    def identify(ip):
        if stop_flag.is_set():
            return None
        dev = {'ip': ip, 'rtt': alive[ip], 'mac': arp.get(ip, local_mac() if ip == my_ip else ''), 'vendor': '', 'dns': reverse_dns(ip),
               'mdns': socket.gethostname() + '.local' if ip == my_ip else mdns_reverse_name(ip), 'netbios': '' if ip == my_ip else netbios_name(ip),
               'services': sorted(services.get(ip, [])), 'upnp': upnp.get(ip, {}).get('server', ''), 'location': upnp.get(ip, {}).get('location', ''), 'ports': probe_ports(ip)}
        dev['name'] = best_name(dev)
        dev['kind'] = guess_kind(dev, my_ip, gateway)
        return dev

    devices = []
    with ThreadPoolExecutor(max_workers=32) as pool:
        for i, dev in enumerate(pool.map(identify, ips)):
            if dev is None or stop_flag.is_set():
                break
            devices.append(dev)
            post(K_FOUND, dev)
            post(K_PHASE, (f'Identified {i + 1}/{len(ips)}: {dev["name"]}', 0.5 + 0.5 * (i + 1) / max(1, len(ips))))
    post(K_DONE, devices)

    # Phase 3 - optional slow online vendor lookup (1/sec), results trickle into the tiles
    if want_vendor:
        for dev in devices:
            if stop_flag.is_set():
                break
            if dev['mac']:
                v = vendor_lookup(dev['mac'])
                if v:
                    post(K_VENDOR_UPDATE, (dev['ip'], v))
                time.sleep(1.1)


# ----------------------------------------------------------------------------------------------------------------------
# Demo - a made-up home network so screenshots never show anyone's real devices
# ----------------------------------------------------------------------------------------------------------------------
def demo_devices():
    """A made-up home network with every kind of device, so every color shows.  192.168.1.x addresses, locally administered MACs (02:...)"""
    def dev(last, name, kind, ports=(), mdns='', dns='', netbios='', services=(), upnp='', vendor='', rtt=1.0):
        return {'ip': f'192.168.1.{last}', 'rtt': rtt, 'mac': f'02:5f:3a:{last:02x}:{last * 37 % 256:02x}:{last * 91 % 256:02x}', 'vendor': vendor, 'dns': dns,
                'mdns': mdns, 'netbios': netbios, 'services': sorted(services), 'upnp': upnp, 'location': '', 'ports': sorted(ports), 'name': name, 'kind': kind}
    return [dev(1, 'router', 'Gateway', (53, 80, 443), dns='router.lan', upnp='Linux/5.4 UPnP/1.0 MiniUPnPd/2.2', vendor='Netgear', rtt=1.2),
            dev(20, 'WORKSTATION', 'This PC', (135, 139, 445, 3389), mdns='workstation.local', netbios='WORKSTATION', vendor='ASUSTek', rtt=0.0),
            dev(21, 'LAPTOP-OFFICE', 'Windows PC', (135, 139, 445), netbios='LAPTOP-OFFICE', dns='laptop-office.lan', vendor='Intel', rtt=2.2),
            dev(22, 'SURFACE-TABLET', 'Windows PC', (135, 445), netbios='SURFACE-TABLET', vendor='Microsoft', rtt=4.0),
            dev(30, 'EPSON-ET-8550', 'Printer', (80, 443, 631, 9100), mdns='EPSON-ET-8550.local', services=('_ipp._tcp', '_printer._tcp'), vendor='Seiko Epson', rtt=3.8),
            dev(31, 'HP-OfficeJet', 'Printer', (80, 631, 9100), mdns='HP-OfficeJet.local', services=('_ipp._tcp',), vendor='HP', rtt=5.1),
            dev(40, 'Kitchen-iPad', 'Apple', (62078,), mdns='Kitchen-iPad.local', services=('_companion-link._tcp',), vendor='Apple', rtt=12.4),
            dev(41, 'Living-Room-Apple-TV', 'Apple', (7000,), mdns='Living-Room-Apple-TV.local', services=('_airplay._tcp', '_raop._tcp'), vendor='Apple', rtt=6.1),
            dev(50, 'nas', 'Linux / NAS', (22, 80, 443, 445, 5000), mdns='nas.local', services=('_afpovertcp._tcp', '_smb._tcp'), vendor='Synology', rtt=0.9),
            dev(51, 'raspberrypi', 'Linux / NAS', (22,), mdns='raspberrypi.local', services=('_ssh._tcp',), vendor='Raspberry Pi Trading', rtt=1.6),
            dev(60, 'Samsung-TV', 'Media / TV', (8008, 8080), upnp='Linux UPnP/1.0 Samsung TV/1.0', vendor='Samsung', rtt=7.3),
            dev(61, 'Chromecast-Bedroom', 'Media / TV', (8008, 8443), mdns='Chromecast-Bedroom.local', services=('_googlecast._tcp',), vendor='Google', rtt=9.8),
            dev(62, 'Sonos-Kitchen', 'Media / TV', (80,), upnp='Linux UPnP/1.0 Sonos/80.1', vendor='Sonos', rtt=4.4),
            dev(70, 'Front-Door-Camera', 'IoT / Camera', (80, 554), vendor='Hikvision', rtt=8.7),
            dev(71, 'ESP-Thermostat', 'IoT / Camera', (80, 1883), vendor='Espressif', rtt=15.2),
            dev(72, 'Tuya-Plug', 'IoT / Camera', (), vendor='Tuya', rtt=18.0),
            dev(90, '192.168.1.90', 'Unknown', (), rtt=None)]


def demo_scan_thread(subnet, want_vendor):
    """The demo's 'scan': the same messages a real scan posts, paced so it looks alive - nothing goes out on the network"""
    for i in range(10):
        if stop_flag.is_set():
            break
        post(K_PHASE, (f'Pinging 254 addresses on {DEMO_SUBNET} ...  (demo - made-up devices)', 0.05 + 0.045 * i))
        time.sleep(0.08)
    found, devices = [], demo_devices()
    for i, dev in enumerate(devices):
        if stop_flag.is_set():
            break
        found.append(dev)
        post(K_FOUND, dev)
        post(K_PHASE, (f'Identified {i + 1}/{len(devices)}: {dev["name"]}', 0.5 + 0.5 * (i + 1) / len(devices)))
        time.sleep(0.06)
    post(K_DONE, found)


# ----------------------------------------------------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------------------------------------------------
def make_tile(dev):
    """One Relay-style tile.  Returns a Frame element (a container, so it may span lines)."""
    color = KIND_COLORS.get(dev['kind'], KIND_COLORS['Unknown'])
    rtt = 'no ping reply' if dev['rtt'] is None else ('local' if dev['kind'] == 'This PC' else f'{dev["rtt"]:.0f} ms')
    ports = ', '.join(COMMON_PORTS[p] for p in dev['ports'][:5]) + (' …' if len(dev['ports']) > 5 else '') if dev['ports'] else 'no open ports found'
    mac_line = (dev['mac'] + ('  ' + dev['vendor'] if dev['vendor'] else '')) if dev['mac'] else 'MAC unknown'
    can_open = not DEMO and bool({80, 443, 8080, 8443} & set(dev['ports']))          # demo addresses are made up - nothing to open
    rows = [[sg.Text(dev['name'][:26], font=FONT_TITLE, text_color=color, background_color=TILE_BG, size=(24, 1), tooltip=dev['name'])],
            [sg.Text(dev['mdns'] or dev['dns'] or ' ', font=FONT_SMALL, text_color=MUTED, background_color=TILE_BG, size=(30, 1))],
            [sg.Text(dev['ip'], font=FONT, text_color=TEXT, background_color=TILE_BG, size=(16, 1)), sg.Text(rtt, font=FONT_SMALL, text_color=MUTED, background_color=TILE_BG)],
            [sg.Text(mac_line, font=FONT_SMALL, text_color=MUTED, background_color=TILE_BG, size=(30, 1), key=('-MAC-', dev['ip']))],
            [sg.Text(ports, font=FONT_SMALL, text_color=MUTED, background_color=TILE_BG, size=(30, 1), tooltip=', '.join(f'{p} {COMMON_PORTS[p]}' for p in dev['ports']))],
            [sg.Text(dev['kind'], font=FONT, text_color=color, background_color=TILE_BG, size=(14, 1)),
             sg.Text('Open', font=FONT, text_color=LINK if can_open else TILE_BG, background_color=TILE_BG, enable_events=can_open, key=KT_OPEN(dev['ip'])),
             sg.Text('Details', font=FONT, text_color=LINK, background_color=TILE_BG, enable_events=True, key=KT_DETAILS(dev['ip']))]]
    return sg.Frame('', rows, background_color=TILE_BG, border_width=1, relief=sg.RELIEF_SOLID, pad=(6, 6), size=(272, 162))


def hidden_kinds():
    return set(sg.user_settings_get_entry(K_HIDDEN_KINDS, []))


def visible_devices(devices):
    hidden = hidden_kinds()
    return [d for d in devices if d['kind'] not in hidden]


def tile_rows(devices, columns):
    shown = visible_devices(devices)
    rows = [[make_tile(d) for d in shown[i:i + columns]] for i in range(0, len(shown), columns)]
    if rows:
        return rows
    msg = 'No devices yet - press Scan' if not devices else 'All device kinds are hidden - click a kind at the top to show it'
    return [[sg.Text(msg, text_color=MUTED, font=FONT, pad=(20, 20))]]


def legend_item(kind):
    """Clickable legend entry. Filled dot + kind color = shown, hollow dot + muted = hidden"""
    on = kind not in hidden_kinds()
    return sg.Text(('● ' if on else '○ ') + kind, key=KT_FILTER(kind), font=FONT_SMALL, text_color=KIND_COLORS[kind] if on else MUTED, pad=(4, 0), enable_events=True,
                   tooltip='Click to hide / show this kind of device')


def count_text(devices):
    shown = len(visible_devices(devices))
    return '' if not devices else (f'{shown} devices' if shown == len(devices) else f'{shown} of {len(devices)} devices shown')


def make_window(devices, location=(None, None), size=(None, None)):
    columns = int(sg.user_settings_get_entry(K_COLUMNS, 4))
    subnet = {'default_text': DEMO_SUBNET} if DEMO else {'setting': local_ip() + '/24'}                  # the demo neither shows nor saves your subnet
    version = f'v{VERSION}' + ('   DEMO - made-up devices' if DEMO else '')
    header = [[sg.Text('Network Scanner', font=FONT_HEADER, text_color='#c4b5fd'), sg.Text(version, font=FONT_SMALL, text_color=MUTED),
               sg.Push(), sg.Text('Subnet', font=FONT), sg.Input(key=K_SUBNET, size=(18, 1), font=FONT, **subnet),
               sg.Text('Columns', font=FONT), sg.Combo([2, 3, 4, 5, 6], key=K_COLUMNS, size=(3, 1), font=FONT, readonly=True, setting=4),
               sg.Checkbox('Online MAC vendor lookup', key=K_VENDOR, font=FONT, setting=True),
               sg.Button('Scan  (F5)', key=K_SCAN, font=FONT, button_color=('black', '#3ddc97')), sg.Button('Stop', key=K_STOP, font=FONT, disabled=True), sg.Button('Diagnose', key=K_DIAG, font=FONT, tooltip='Collect raw network info to explain an empty scan')],
              [sg.Text('Click a kind to hide / show:', font=FONT_SMALL, text_color=MUTED), *[legend_item(k) for k in KIND_COLORS], sg.Push(), sg.Text('', font=FONT_SMALL, text_color=MUTED, key=K_COUNT)]]
    if size == (None, None):
        size = (columns * 284 + 60, 860)
    layout = [*header,
              [sg.Column(tile_rows(devices, columns), key=K_GRID, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True, background_color=BG, size=(None, 600))],
              [sg.ProgressBar(100, orientation='h', size=(30, 10), key=K_PROGRESS, expand_x=True, bar_color=('#3ddc97', TILE_BORDER))],
              [sg.Text('Ready.  Press Scan to discover devices on the local network.', key=K_STATUS, font=FONT_SMALL, text_color=MUTED, size=(100, 1))]]
    title = 'Network Scanner' + (' - demo' if DEMO else '')
    window = sg.Window(title, layout, location=location, size=size, resizable=True, finalize=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT,
                       enable_close_attempted_event=True, margins=(10, 8), font=FONT)
    for key in ('<Up>', '<Down>', '<Prior>', '<Next>', '<Home>', '<End>', '<Escape>', '<F5>'):
        window.bind(key, key)
    window[K_COUNT].update(count_text(devices))
    return window


def scroll_grid(window, event):
    canvas = window[K_GRID].Widget.canvas
    if event == '<Up>':
        canvas.yview_scroll(-1, 'units')
    elif event == '<Down>':
        canvas.yview_scroll(1, 'units')
    elif event == '<Prior>':
        canvas.yview_scroll(-1, 'pages')
    elif event == '<Next>':
        canvas.yview_scroll(1, 'pages')
    elif event == '<Home>':
        canvas.yview_moveto(0)
    elif event == '<End>':
        canvas.yview_moveto(1)


def details_text(dev):
    ping_txt = 'no reply' if dev['rtt'] is None else '{:.1f} ms'.format(dev['rtt'])
    lines = [f'Name:        {dev["name"]}', f'Kind:        {dev["kind"]}', f'IP:          {dev["ip"]}', f'Ping:        {ping_txt}',
             f'MAC:         {dev["mac"] or "unknown"}', f'Vendor:      {dev["vendor"] or "unknown"}', f'mDNS name:   {dev["mdns"] or "-"}', f'DNS name:    {dev["dns"] or "-"}',
             f'NetBIOS:     {dev["netbios"] or "-"}', f'UPnP server: {dev["upnp"] or "-"}', f'UPnP URL:    {dev["location"] or "-"}',
             'mDNS svcs:   ' + (', '.join(dev['services']) or '-'), 'Open ports:  ' + (', '.join(f'{p} ({COMMON_PORTS[p]})' for p in dev['ports']) or 'none of the common ports')]
    return '\n'.join(lines)


def replace_window(old, devices):
    """Rebuild the tile grid by replacing the window at the same place and size.  The new window is published to the worker threads
    BEFORE the old one closes, then the doorbell is re-rung if mail is waiting, so a ring that landed on the old window is not lost."""
    new = make_window(devices, location=old.current_location(), size=old.size)
    AppWin.current = new
    old.close()
    if not mailbox.empty():
        new.write_event_value(K_MAIL, None)
    return new


def main():
    sg.user_settings_filename(filename='network_scanner.json')
    devices, pending = [], []
    window = AppWin.current = make_window(devices)
    scanning, progress = False, 0
    if DEMO:
        window.write_event_value(K_SCAN, None)                      # the demo starts by itself

    while True:
        event, values = window.read()
        value = None
        if event == K_MAIL:                                           # one thread message per pass, re-ring while more are waiting
            try:
                event, value = mailbox.get_nowait()
            except queue.Empty:
                continue
            if not mailbox.empty():
                window.write_event_value(K_MAIL, None)
        if event in ('Exit', sg.WINDOW_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, '<Escape>'):
            stop_flag.set()
            if not DEMO:
                window.settings_save(values)
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event in ('<Up>', '<Down>', '<Prior>', '<Next>', '<Home>', '<End>'):
            scroll_grid(window, event)
        elif event in (K_SCAN, '<F5>') and not scanning:
            scanning, pending = True, []
            stop_flag.clear()
            if not DEMO:
                window.settings_save(values)
            window[K_SCAN].update(disabled=True)
            window[K_STOP].update(disabled=False)
            window[K_COUNT].update('')
            threading.Thread(target=demo_scan_thread if DEMO else scan_thread, args=(values[K_SUBNET].strip(), values[K_VENDOR]), daemon=True).start()
        elif event == K_DIAG:
            window[K_STATUS].update('Running diagnostics (about 10 s) ...')
            threading.Thread(target=lambda: post(K_DIAG_DONE, diagnostics()), daemon=True).start()
        elif event == K_DIAG_DONE:
            report = value
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'network_scanner_diag.txt')
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(report)
                window[K_STATUS].update(f'Diagnostics saved to {path}')
            except Exception as e:
                window[K_STATUS].update(f'Could not save diagnostics: {e}')
            sg.popup_scrolled(report, title='Network diagnostics - saved to ' + path, font=('Consolas', 9), size=(120, 40), keep_on_top=True, non_blocking=True)
        elif event == K_STOP:
            stop_flag.set()
            window[K_STATUS].update('Stopping ...')
        elif event == K_PHASE:
            text, frac = value
            progress = int(frac * 100)
            window[K_STATUS].update(text)
            window[K_PROGRESS].update(progress)
        elif event == K_FOUND:
            pending.append(value)
            window[K_COUNT].update(f'{len(pending)} devices identified')
        elif event == K_DONE:                                         # rebuild sorted grid in a fresh window (same place / size)
            scanning, progress = False, 100
            devices = value
            vendor_on = values[K_VENDOR]
            window = replace_window(window, devices)
            if DEMO:
                window[K_STATUS].update(f'Demo: {len(devices)} made-up devices - nothing on your network was scanned.')
            else:
                window[K_STATUS].update(f'Scan complete: {len(devices)} devices.' + ('  Looking up MAC vendors online ...' if vendor_on and devices else ''))
            window[K_PROGRESS].update(100)
        elif isinstance(event, tuple) and event[0] == K_FILTER:         # toggle a kind on/off, then rebuild the grid
            hidden = hidden_kinds()
            hidden.symmetric_difference_update({event[1]})
            sg.user_settings_set_entry(K_HIDDEN_KINDS, sorted(hidden))
            status = window[K_STATUS].get()
            window = replace_window(window, devices)
            window[K_STATUS].update(status)
            window[K_PROGRESS].update(progress)
            if scanning:                                                # a scan is still running - keep its buttons and live count
                window[K_SCAN].update(disabled=True)
                window[K_STOP].update(disabled=False)
                window[K_COUNT].update(f'{len(pending)} devices identified')
        elif event == K_VENDOR_UPDATE:
            ip, vendor = value
            for d in devices:
                if d['ip'] == ip:
                    d['vendor'] = vendor
                    if d['kind'] not in hidden_kinds():
                        window[('-MAC-', ip)].update(d['mac'] + '  ' + vendor)
        elif isinstance(event, tuple) and event[0] == K_TILE_DETAILS:
            dev = next((d for d in devices if d['ip'] == event[1]), None)
            if dev:
                sg.popup_scrolled(details_text(dev), title=dev['name'], font=('Consolas', 10), size=(80, 16), keep_on_top=True, non_blocking=True)
        elif isinstance(event, tuple) and event[0] == K_TILE_OPEN:
            dev = next((d for d in devices if d['ip'] == event[1]), None)
            if dev:
                webbrowser.open(('https://' if 443 in dev['ports'] and 80 not in dev['ports'] else 'http://') + dev['ip'] + (':8080' if dev['ports'] and 80 not in dev['ports'] and 8080 in dev['ports'] else ''))
    window.close()


if __name__ == '__main__':
    main()
