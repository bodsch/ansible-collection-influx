# coding: utf-8
from __future__ import annotations, unicode_literals

import pytest
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="all")

# --- tests -----------------------------------------------------------------

# _facts = local_facts(host=host, fact="influxdb3")

def test_version_influxd(host, get_vars):
    """
    """
    _facts = local_facts(host=host, fact="influxdb3")

    version = _facts.get("version", {})
    influxd_version = version.get("core", None)

    version_dir = f"/opt/influxd/{influxd_version}"
    current_link = "/usr/bin/influxdb3"

    print(version)
    print(influxd_version)
    print(version_dir)

    directory = host.file(version_dir)
    assert directory.is_directory

    link  = host.file(current_link)
    assert link.is_symlink
    assert link.linked_to == f"{version_dir}/influxdb3"


@pytest.mark.parametrize("directories", [
    "/var/lib/influxdb3",
    "/var/lib/influxdb3/wal",
    "/var/lib/influxdb3/data",
    "/var/lib/influxdb3/meta",
])
def test_directories(host, directories):

    d = host.file(directories)
    assert d.is_directory


def test_files(host, get_vars):
    """
    """
    distribution = host.system_info.distribution
    release = host.system_info.release

    files = []
    # files.append("/etc/influxdb3/config.yml")

    if not distribution == "artix":
        files.append("/etc/default/influxdb3")

    for _file in files:
        f = host.file(_file)
        assert f.is_file


def test_service_running_and_enabled(host):
    service = host.service('influxdb3')
    assert service.is_running
    assert service.is_enabled


def test_listening_socket(host, get_vars):
    """
    """
    listening = host.socket.get_listening_sockets()

    for i in listening:
        print(i)

    bind_address = "127.0.0.1"
    bind_port = 8181

    listen = []
    listen.append(f"tcp://{bind_address}:{bind_port}")

    for spec in listen:
        socket = host.socket(spec)
        assert socket.is_listening
