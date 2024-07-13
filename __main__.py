from .server import app, my_ip_address
from zeroconf import ServiceInfo, Zeroconf, IPVersion
import socket

this_host = my_ip_address()
print("This host: {}".format(this_host))

info = ServiceInfo(
    "_http._tcp.local.",
    "drive-thru._http._tcp.local.",
    addresses=[socket.inet_aton(this_host)],
    port=5000,
    properties={},
    server="drive-thru.local."
)

zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
zeroconf.register_service(info, ttl=3, cooperating_responders=True)

app.run(host=this_host)