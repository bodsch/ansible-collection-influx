# coding: utf-8
from __future__ import annotations, unicode_literals

import pytest
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------

# _facts = local_facts(host=host, fact="telegraf")

@pytest.mark.parametrize("dirs", [
    "/etc/telegraf",
    "/etc/telegraf/telegraf.d",
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory


def test_telegraf_files(host, get_vars):
    """
    """
    distribution = host.system_info.distribution
    release = host.system_info.release

    _facts = local_facts(host=host, fact="telegraf")
    version = _facts.get("version", {})

    print(f"distribution: {distribution}")
    print(f"release     : {release}")
    print(f"version     : {version}")

    install_dir = get_vars.get("telegraf_install_path")
    defaults_dir = get_vars.get("telegraf_defaults_directory")
    config_dir = get_vars.get("telegraf_config_dir")

    if 'latest' in install_dir:
        install_dir = install_dir.replace('latest', version)

    files = []
    files.append("/usr/bin/telegraf")

    if install_dir:
        files.append(f"{install_dir}/telegraf")
    if defaults_dir and not distribution == "artix":
        files.append(f"{defaults_dir}/telegraf")
    if config_dir:
        files.append(f"{config_dir}/telegraf.conf")

    print(files)

    for _file in files:
        f = host.file(_file)
        assert f.is_file


def test_user(host, get_vars):
    """
    """
    user = get_vars.get("telegraf_system_user", "telegraf")
    group = get_vars.get("telegraf_system_group", "telegraf")

    assert host.group(group).exists
    assert host.user(user).exists
    assert group in host.user(user).groups
    assert host.user(user).home == "/nonexistent"


def test_service(host, get_vars):
    service = host.service("telegraf")
    assert service.is_enabled
    assert service.is_running
