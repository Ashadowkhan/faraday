import json
import logging
import socket
import sqlalchemy
from datetime import datetime

from faraday.searcher.api import ApiError
from faraday.server.api.modules.vulns import VulnerabilitySchema, VulnerabilityWebSchema
from faraday.server.models import Workspace, Vulnerability, VulnerabilityWeb, Service, Host, Command

logger = logging.getLogger('Faraday searcher')


class SqlApi:
    def __init__(self, workspace_name, test_cient=None, session=None):
        self.session = session
        self.command_id = None  # Faraday uses this to tracker searcher changes.
        workspace = self.session.query(Workspace).filter_by(name=workspace_name).all()
        if len(workspace) > 0:
            self.workspace = workspace[0]
        else:
            raise ApiError("Workspace %s doesn't exist" % workspace_name)

    def create_command(self, itime, params, tool_name):
        self.itime = itime
        self.params = params
        self.tool_name = tool_name
        data = self._command_info()

        command = Command(**data)
        self.session.add(command)
        self.session.flush()

        return command.id

    def _command_info(self, duration=None):
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            ip = socket.gethostname()
        data = {
            "start_date": datetime.fromtimestamp(self.itime),
            "command": self.tool_name,
            "ip": ip,
            "import_source": "shell",
            "tool": "Searcher",
            "params": json.dumps(self.params),
            "workspace_id": self.workspace.id
        }
        if duration:
            data.update({"duration": duration})
        return data

    def close_command(self, command_id, duration):
        data = self._command_info(duration)
        command = Command.query.get(command_id)
        if command:
            for (key, value) in data.iteritems():
                setattr(command, key, value)
            self.session.commit()

    def fetch_vulnerabilities(self):
        vulnerabilities = self.session.query(Vulnerability, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)

        vulnerabilities = [vulnerability for vulnerability, pos in
                           vulnerabilities.distinct(Vulnerability.id)]

        vulnerabilities = VulnerabilitySchema(many=True).dumps(vulnerabilities)
        vulnerabilities_data = json.loads(vulnerabilities.data)

        web_vulnerabilities = self.session.query(Vulnerability, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)

        web_vulnerabilities = [web_vulnerability for web_vulnerability, pos in
                               web_vulnerabilities.distinct(VulnerabilityWeb.id)]

        web_vulnerabilities = VulnerabilityWebSchema(many=True).dumps(web_vulnerabilities)
        web_vulnerabilities_data = json.loads(web_vulnerabilities.data)

        return vulnerabilities_data + web_vulnerabilities_data

    def fetch_services(self):
        services = self.session.query(Service, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        services = [service for service, pos in
                    services.distinct(Service.id)]
        return services

    def fetch_hosts(self):
        hosts = self.session.query(Host, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        hosts = [host for host, pos in
                 hosts.distinct(Host.id)]
        return hosts

    def filter_vulnerabilities(self, **kwargs):
        vulnerabilities = []
        vulnerabilities_query = self.session.query(Vulnerability, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        for attr, value in kwargs.iteritems():
            if attr == 'regex':
                vulnerabilities_query = vulnerabilities_query.filter(Vulnerability.name.op('~')(value))
                vulnerabilities = [vulnerability for vulnerability, pos in
                                   vulnerabilities_query.distinct(Vulnerability.id)]
            elif hasattr(Vulnerability, attr):
                vulnerabilities_query = vulnerabilities_query.filter(getattr(Vulnerability, attr) == value)
                vulnerabilities = [vulnerability for vulnerability, pos in
                                   vulnerabilities_query.distinct(Vulnerability.id)]

        web_vulnerabilities = []
        web_vulnerabilities_query = self.session.query(Vulnerability, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        for attr, value in kwargs.iteritems():
            if attr == 'regex':
                web_vulnerabilities_query = web_vulnerabilities_query.filter(VulnerabilityWeb.name.op('~')(value))
                web_vulnerabilities = [web_vulnerability for web_vulnerability, pos in
                                       web_vulnerabilities_query.distinct(VulnerabilityWeb.id)]
            elif hasattr(VulnerabilityWeb, attr):
                web_vulnerabilities_query = web_vulnerabilities_query.filter(getattr(VulnerabilityWeb, attr) == value)
                web_vulnerabilities = [web_vulnerability for web_vulnerability, pos in
                                       web_vulnerabilities_query.distinct(Vulnerability.id)]

        return list(set(vulnerabilities + web_vulnerabilities))

    def filter_services(self, **kwargs):
        services = []
        services_query = self.session.query(Service, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        for attr, value in kwargs.iteritems():
            if attr == 'regex':
                services_query = services_query.filter(Service.name.op('~')(value))
                services = [service for service, pos in
                            services_query.distinct(Service.id)]
            elif hasattr(Service, attr):
                services_query = services_query.filter(getattr(Service, attr) == value)
                services = [service for service, pos in
                            services_query.distinct(Service.id)]

        return services

    def filter_hosts(self, **kwargs):
        hosts = []
        hosts_query = self.session.query(Host, Workspace.id).join(Workspace).filter(
            Workspace.name == self.workspace.name)
        for attr, value in kwargs.iteritems():
            if attr == 'regex':
                hosts_query = hosts_query.filter(Host.ip.op('~')(value))
                hosts = [host for host, pos in
                         hosts_query.distinct(Host.id)]
            elif hasattr(Host, attr):
                hosts_query = hosts_query.filter(getattr(Host, attr) == value)
                hosts = [host for host, pos in
                         hosts_query.distinct(Host.id)]

        return hosts

    def update_vulnerability(self, vulnerability):
        # try:
        #     vuln = None
        #     if isinstance(vulnerability, Vulnerability):
        #         vuln = Vulnerability.query.get(vulnerability.id)
        #     if isinstance(vulnerability, VulnerabilityWeb):
        #         vuln = VulnerabilityWeb.query.get(vulnerability.id)
        #
        #     for (key, value) in vars(vulnerability).iteritems():
        #         setattr(vuln, key, value)
        #     self.session.commit()
        # except sqlalchemy.exc.IntegrityError as ex:
        #     self.session.rollback()
        #     logger.error(str(ex))
        #     return False
        # return vulnerability
        vulnerability.severity = 'informational'
        self.session.commit()

    def update_service(self, service):
        pass

    def update_host(self, host):
        pass

    def delete_vulnerability(self, vulnerability_id):
        vuln = Vulnerability.query.get(vulnerability_id)
        if vuln is None:
            vuln = VulnerabilityWeb.query.get(vulnerability_id)
        self.session.delete(vuln)
        self.session.commit()

    def delete_service(self, service_id):
        service = Service.query.get(service_id)
        if service:
            self.session.delete(service)
            self.session.commit()

    def delete_host(self, host_id):
        host = Service.query.get(host_id)
        if host:
            self.session.delete(host)
            self.session.commit()

    @staticmethod
    def intersection(objects, models):
        return list(set(objects).intersection(set(models)))
