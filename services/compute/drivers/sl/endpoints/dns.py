import falcon
import json
import urllib.parse

from SoftLayer import DNSManager

from services.common.nested_dict import lookup


class SLComputeV2DNSDomains(object):
    def on_get(self, req, resp, tenant_id):
        client = req.env['sl_client']
        mgr = DNSManager(client)

        results = []

        for zone in mgr.list_zones():
            results.append({
                'project': None,
                'scope': 'public',
                'domain': zone['name'],
                'availability_zone': None,
            })

        resp.body = json.dumps({'domain_entries': results})


class SLComputeV2DNSDomainEntry(object):
    def on_delete(self, req, resp, tenant_id, domain, entry):
        client = req.env['sl_client']
        mgr = DNSManager(client)

        domain = urllib.parse.unquote_plus(domain)

        zone_id = mgr._get_zone_id_from_name(domain)[0]

        record = mgr.get_records(zone_id, host=entry)[0]

        mgr.delete_record(record['id'])

        resp.status = falcon.HTTP_204

    def on_get(self, req, resp, tenant_id, domain, entry=None):
        client = req.env['sl_client']
        mgr = DNSManager(client)

        domain = urllib.parse.unquote_plus(domain)

        zone_id = mgr._get_zone_id_from_name(domain)[0]

        if entry:
            record = mgr.get_records(zone_id, host=entry)[0]

        result = get_dns_entry_dict(domain, record['host'], record['data'],
                                    record['type'], record['id'])

        resp.body = json.dumps({'dns_entry': result})


    def on_put(self, req, resp, tenant_id, domain, entry):
        client = req.env['sl_client']
        mgr = DNSManager(client)

        body = json.loads(req.stream.read().decode())

        ip = lookup(body, 'dns_entry', 'ip')

        record_type = lookup(body, 'dns_entry', 'type')

        if not record_type:
            record_type = 'A'

        domain = urllib.parse.unquote_plus(domain)

        zone_id = mgr._get_zone_id_from_name(domain)[0]

        mgr.create_record(zone_id=zone_id, record=entry, type=record_type,
                          data=ip)

        new_record = mgr.get_records(zone_id, host=entry)[0]

        result = get_dns_entry_dict(domain, entry, ip, record_type,
                                    new_record['id'])

        resp.body = json.dumps({'dns_entry': result})


def get_dns_entry_dict(domain, name, ip, type, id=None):
    return {
        'ip': ip,
        'domain': domain,
        'type': type,
        'id': id,
        'name': name,
    }
