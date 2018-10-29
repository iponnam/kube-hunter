import logging
import os
import commands


from ...core.events import handler
from ...core.events.types import Vulnerability, Event
from ...core.types import ActiveHunter, KubernetesCluster, AccessRisk
from ..discovery.hosts import RunningAsPodEvent


""" Vulnerabilities """
class InstallPackages(Vulnerability, Event):
    """Installing Packages would grant an attacker the option to run exploitation tools from within the compromised pod"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Installing Linux Packages From Within a Compromised Pod",
                               category=AccessRisk)
        self.evidence = evidence


class PrivilegedPod(Vulnerability, Event):
    """Running from a privileged pod might grant an attacker the option control the whole cluster"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Privileged Pod might can grant an attacker full control over the cluster",
                               category=AccessRisk)
        self.evidence = evidence


# Passive Hunter
@handler.subscribe(RunningAsPodEvent)
class InstallPackagesHunter(ActiveHunter):
    """Installing Packages would grant an attacker the option to run exploitation tools from within the compromised pod"""

    def __init__(self, event):
        self.event = event
        self.packages_installation_available = ''
        self.is_root = False

    def attempt_to_install_packages_system_wide(self):
        logging.debug(self.event.host)
        logging.debug('Passive Hunter is attempting to install portable apps')
        res1, res2 = False
        # get all files and subdirectories files:
        if self.is_root:
            res1 = commands.getstatusoutput('apt-get install') if commands.getstatusoutput('apt-get install 2> error.txt | cat error.txt') == '' else False
        else:
            res2 = commands.getstatusoutput('sudo apt-get install') if commands.getstatusoutput('sudo apt-get install 2> error.txt | cat error.txt') == '' else False
        return res1 or '[sudo] password for' not in res2  #  If that string is in res2 it means we were asked for password we dont know and we couldnt install any tools..

    def is_privileged_pod(self):
        self.is_root = commands.getstatusoutput('id-u') == '0'
        return self.is_root

    def execute(self):
        if self.is_privileged_pod():
            self.publish_event(PrivilegedPod(self.is_root))

        if self.attempt_to_install_packages_system_wide():
            self.publish_event(InstallPackages(self.packages_installation_available))

