
# Ansible Role:  `influxdb`

Ansible role to install and configure [influxdb2](https://github.com/influxdata/influxdb).

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-influxdb/main.yml?branch=main)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-influxdb)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-influxdb)][releases]
[![Ansible Downloads](https://img.shields.io/ansible/role/d/bodsch/influxdb?logo=ansible)][galaxy]

[ci]: https://github.com/bodsch/ansible-influxdb/actions
[issues]: https://github.com/bodsch/ansible-influxdb/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-influxdb/releases
[galaxy]: https://galaxy.ansible.com/ui/standalone/roles/bodsch/influxdb


This role installs, manages and configures (**ONLY**) InfluxDB2.

Pull-Requests and Issues are welcome :)


If `latest` is set for `influxdb3_version`, the role tries to install the latest release version.
**Please use this with caution, as incompatibilities between releases may occur!**

The `influxd` binary are installed below `/opt/influxd/${influxdb3_version}` and later linked to `/usr/bin`.  
The `influx` binary are installed below `/opt/influx/${influxdb3_cli_version}` and later linked to `/usr/bin`.  
This should make it possible to downgrade relatively safely.

The downloaded archive is stored on the Ansible controller, unpacked and then the binaries are copied to the target system.
The cache directory can be defined via the environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`.
By default it is `${HOME}/.cache/ansible/influxdb`.

If this type of installation is not desired, the download can take place directly on the target system.
However, this must be explicitly activated by setting `influxdb3_direct_download` to `true`.

## Requirements & Dependencies

Ansible Collections

- [bodsch.core](https://github.com/bodsch/ansible-collection-core)
- [bodsch.scm](https://github.com/bodsch/ansible-collection-scm)

```bash
ansible-galaxy collection install bodsch.core
ansible-galaxy collection install bodsch.scm
```
or
```bash
ansible-galaxy collection install --requirements-file collections.yml
```


## Operating systems

Tested on

* Arch Linux
* Artix Linux
* Debian based
    - Debian 10 / 11 / 12
    - Ubuntu 20.10 / 22.04

> **RedHat-based systems are no longer officially supported! May work, but does not have to.**


## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-influxdb/tags)!


## Configuration

```yaml
# see: https://docs.influxdata.com/influxdb/v2/reference/release-notes/influxdb/
influxdb3_version: "3.0.0"

influxdb3_release: {}
  # download_url: ""
  # api_url: ""
  # files:
  #   influxdb: ""
  #   influx_client: ""
  # binaries:
  #   influxd: ""
  #   influx: ""

influxdb3_system_user: influxdb
influxdb3_system_group: influxdb
influxdb3_config_dir: /etc/influxdb3
influxdb3_storage_dir: /var/lib/influxdb3

influxdb3_direct_download: false

influxdb3_serve: {}

# InfluxDB 3 native databases (only used when influxdb3_main_version == 3)
influxdb3_databases: {}
```


### `influxdb3_release`

Only needed to download the binary archives.

Default configuration:

```yaml
influxdb3_release:
  download_url: "https://dl.influxdata.com/influxdb/releases"
  api_url: ""
  files:
    influxdb: "{{ influxdb3_bin_version }}-{{ influxdb3_version }}-{{ ansible_facts.system | lower }}-{{ system_architecture }}.tar.gz"
    influx_client: "{{ influxdb3_bin_version }}-client-{{ influxdb3_cli_version }}-{{ ansible_facts.system | lower }}-{{ system_architecture }}.tar.gz"
  binaries:
    influxd: "influxd"
    influx: "influx"
```

### `influxdb3_service`


```yaml
influxdb3_serve:
  # --node-id  [env: INFLUXDB3_NODE_IDENTIFIER_PREFIX]  (since 3.0.0, REQUIRED)
  # Node identifier used as prefix in object store file paths.
  node_id: "{{ ansible_facts.hostname }}"

  # --num-io-threads  [env: INFLUXDB3_NUM_IO_THREADS]  (since 3.1.0)
  # GLOBAL option: rendered BEFORE the `serve` subcommand.
  num_io_threads: ""

  # ---------------------------------------------------------------- object store / storage
  object_store:
    # --object-store  [env: INFLUXDB3_OBJECT_STORE]  (since 3.0.0, default: memory)
    # possible: memory | memory-throttled | file | s3 | google | azure
    type: file
    # --bucket  [env: INFLUXDB3_BUCKET]  (since 3.0.0) - cloud object storage bucket
    bucket: ""
    # --object-store-connection-limit  [env: INFLUXDB3_OBJECT_STORE_CONNECTION_LIMIT]  (since 3.0.0, default: 16)
    connection_limit: ""
    # --object-store-http2-only  [env: INFLUXDB3_OBJECT_STORE_HTTP2_ONLY]  (since 3.0.0) - SWITCH
    http2_only: false
    # --object-store-http2-max-frame-size  [env: INFLUXDB3_OBJECT_STORE_HTTP2_MAX_FRAME_SIZE]  (since 3.0.0)
    http2_max_frame_size: ""
    # --object-store-max-retries  [env: INFLUXDB3_OBJECT_STORE_MAX_RETRIES]  (since 3.0.0)
    max_retries: ""
    # --object-store-retry-timeout  [env: INFLUXDB3_OBJECT_STORE_RETRY_TIMEOUT]  (since 3.0.0)
    retry_timeout: ""
    # --object-store-cache-endpoint  [env: INFLUXDB3_OBJECT_STORE_CACHE_ENDPOINT]  (since 3.0.0)
    cache_endpoint: ""
    # --object-store-request-timeout  [env: INFLUXDB3_OBJECT_STORE_REQUEST_TIMEOUT]  (since 3.6.0, default: 30s)
    request_timeout: ""
    # --object-store-tls-allow-insecure  [env: INFLUXDB3_OBJECT_STORE_TLS_ALLOW_INSECURE]  (since 3.5.0) - SWITCH
    tls_allow_insecure: false
    # --object-store-tls-ca  [env: INFLUXDB3_OBJECT_STORE_TLS_CA]  (since 3.5.0)
    tls_ca: ""
    aws:
      access_key_id: ""       # --aws-access-key-id      [env: AWS_ACCESS_KEY_ID]      (since 3.0.0)
      secret_access_key: ""   # --aws-secret-access-key  [env: AWS_SECRET_ACCESS_KEY]  (since 3.0.0)
      default_region: ""      # --aws-default-region     [env: AWS_DEFAULT_REGION]     (since 3.0.0, default: us-east-1)
      endpoint: ""            # --aws-endpoint           [env: AWS_ENDPOINT]           (since 3.0.0)
      session_token: ""       # --aws-session-token      [env: AWS_SESSION_TOKEN]      (since 3.0.0)
      allow_http: false       # --aws-allow-http         [env: AWS_ALLOW_HTTP]         (since 3.0.0) - SWITCH
      skip_signature: false   # --aws-skip-signature     [env: AWS_SKIP_SIGNATURE]     (since 3.0.0) - SWITCH
      credentials_file: ""    # --aws-credentials-file   [env: AWS_CREDENTIALS_FILE]   (since 3.2.0)
    google:
      service_account: ""     # --google-service-account [env: GOOGLE_SERVICE_ACCOUNT] (since 3.0.0)
    azure:
      storage_account: ""     # --azure-storage-account    [env: AZURE_STORAGE_ACCOUNT]    (since 3.0.0)
      storage_access_key: ""  # --azure-storage-access-key [env: AZURE_STORAGE_ACCESS_KEY] (since 3.0.0)
      endpoint: ""            # --azure-endpoint           [env: AZURE_ENDPOINT]           (since 3.4.0)
      allow_http: false       # --azure-allow-http         [env: AZURE_ALLOW_HTTP]         (since 3.4.0) - SWITCH

  # ---------------------------------------------------------------- http / network
  http:
    # --http-bind  [env: INFLUXDB3_HTTP_BIND_ADDR]  (since 3.0.0, default: 0.0.0.0:8181)
    bind: "127.0.0.1:8181"
    # --max-http-request-size  [env: INFLUXDB3_MAX_HTTP_REQUEST_SIZE]  (since 3.0.0, default: 10485760)
    max_request_size: ""
  # --tcp-listener-file-path  [env: INFLUXDB3_TCP_LISTENER_FILE_PATH]  (since 3.1.0)
  tcp_listener_file_path: ""

  # ---------------------------------------------------------------- TLS
  tls:
    cert: ""             # --tls-cert             [env: INFLUXDB3_TLS_CERT]             (since 3.0.0)
    key: ""              # --tls-key              [env: INFLUXDB3_TLS_KEY]              (since 3.0.0)
    minimum_version: ""  # --tls-minimum-version  [env: INFLUXDB3_TLS_MINIMUM_VERSION]  (since 3.0.2, default: tls-1.2)

  # ---------------------------------------------------------------- auth / authz
  auth:
    # Renders --without-auth  [env: INFLUXDB3_START_WITHOUT_AUTH]  (since 3.0.0) when disabled.
    enabled: false
    # --disable-authz  [env: INFLUXDB3_DISABLE_AUTHZ]  (since 3.1.0)
    # list of resources, e.g. [health, ping, metrics, ready, pprof]
    disable_authz: []
    # --admin-token-file  [env: INFLUXDB3_ADMIN_TOKEN_FILE]  (since 3.4.0)
    admin_token_file: ""
    # --admin-token-recovery-http-bind  [env: INFLUXDB3_ADMIN_TOKEN_RECOVERY_HTTP_BIND]  (since 3.3.0, default: 127.0.0.1:8182)
    admin_token_recovery_http_bind: ""
    # --admin-token-recovery-tcp-listener-file-path  (since 3.3.0)
    admin_token_recovery_tcp_listener_file_path: ""

  # ---------------------------------------------------------------- query / resource limits
  query:
    file_limit: ""      # --query-file-limit       [env: INFLUXDB3_QUERY_FILE_LIMIT]       (since 3.0.0, default: 432)
    log_size: ""        # --query-log-size         [env: INFLUXDB3_QUERY_LOG_SIZE]         (since 3.0.0, default: 1000)
    max_concurrent: ""  # --max-concurrent-queries [env: INFLUXDB3_MAX_CONCURRENT_QUERIES] (since 3.10.0)

  # ---------------------------------------------------------------- memory
  memory:
    exec_mem_pool_bytes: ""           # --exec-mem-pool-bytes          [env: INFLUXDB3_EXEC_MEM_POOL_BYTES]          (since 3.0.0)
    force_snapshot_mem_threshold: ""  # --force-snapshot-mem-threshold [env: INFLUXDB3_FORCE_SNAPSHOT_MEM_THRESHOLD] (since 3.0.0, default: 70%)

  # ---------------------------------------------------------------- write-ahead log (WAL)
  wal:
    flush_interval: ""             # --wal-flush-interval           [env: INFLUXDB3_WAL_FLUSH_INTERVAL]            (since 3.0.0, default: 1s)
    snapshot_size: ""              # --wal-snapshot-size            [env: INFLUXDB3_WAL_SNAPSHOT_SIZE]             (since 3.0.0, default: 600)
    max_write_buffer_size: ""      # --wal-max-write-buffer-size    [env: INFLUXDB3_WAL_MAX_WRITE_BUFFER_SIZE]     (since 3.0.0, default: 100000)
    snapshotted_files_to_keep: ""  # --snapshotted-wal-files-to-keep [env: INFLUXDB3_NUM_WAL_FILES_TO_KEEP]        (since 3.0.0, default: 300)
    replay_fail_on_error: false    # --wal-replay-fail-on-error     [env: INFLUXDB3_WAL_REPLAY_FAIL_ON_ERROR]      (since 3.2.0) - SWITCH
    replay_concurrency_limit: ""   # --wal-replay-concurrency-limit [env: INFLUXDB3_WAL_REPLAY_CONCURRENCY_LIMIT]  (since 3.2.0)
  # --checkpoint-interval  [env: INFLUXDB3_CHECKPOINT_INTERVAL]  (since 3.8.2)
  checkpoint_interval: ""

  # ---------------------------------------------------------------- compaction / data lifecycle
  compaction:
    gen1_duration: ""           # --gen1-duration          [env: INFLUXDB3_GEN1_DURATION]          (since 3.0.0, default: 10m)
    gen1_lookback_duration: ""  # --gen1-lookback-duration [env: INFLUXDB3_GEN1_LOOKBACK_DURATION] (since 3.2.0, default: 24h)
  retention:
    check_interval: ""                # --retention-check-interval       [env: INFLUXDB3_RETENTION_CHECK_INTERVAL]       (since 3.3.0, default: 30m)
    delete_grace_period: ""           # --delete-grace-period            [env: INFLUXDB3_DELETE_GRACE_PERIOD]            (since 3.2.0, default: 24h)
    hard_delete_default_duration: ""  # --hard-delete-default-duration   [env: INFLUXDB3_HARD_DELETE_DEFAULT_DURATION]   (since 3.2.0, default: 90d)

  # ---------------------------------------------------------------- caches
  cache:
    parquet_mem_cache_size: ""                 # --parquet-mem-cache-size                [env: INFLUXDB3_PARQUET_MEM_CACHE_SIZE]                (since 3.0.0, default: 20%)
    parquet_mem_cache_prune_percentage: ""     # --parquet-mem-cache-prune-percentage    [env: INFLUXDB3_PARQUET_MEM_CACHE_PRUNE_PERCENTAGE]    (since 3.0.0, default: 0.1)
    parquet_mem_cache_prune_interval: ""       # --parquet-mem-cache-prune-interval      [env: INFLUXDB3_PARQUET_MEM_CACHE_PRUNE_INTERVAL]      (since 3.0.0, default: 1s)
    parquet_mem_cache_query_path_duration: ""  # --parquet-mem-cache-query-path-duration [env: INFLUXDB3_PARQUET_MEM_CACHE_QUERY_PATH_DURATION] (since 3.0.0, default: 5h)
    disable_parquet_mem_cache: false           # --disable-parquet-mem-cache             [env: INFLUXDB3_DISABLE_PARQUET_MEM_CACHE]             (since 3.0.0) - SWITCH
    last_cache_eviction_interval: ""           # --last-cache-eviction-interval          [env: INFLUXDB3_LAST_CACHE_EVICTION_INTERVAL]          (since 3.0.0, default: 10s)
    distinct_cache_eviction_interval: ""       # --distinct-cache-eviction-interval      [env: INFLUXDB3_DISTINCT_CACHE_EVICTION_INTERVAL]      (since 3.0.0, default: 10s)
    table_index_cache_max_entries: ""          # --table-index-cache-max-entries         [env: INFLUXDB3_TABLE_INDEX_CACHE_MAX_ENTRIES]         (since 3.3.0, default: 1000)
    table_index_cache_concurrency_limit: ""    # --table-index-cache-concurrency-limit   [env: INFLUXDB3_TABLE_INDEX_CACHE_CONCURRENCY_LIMIT]   (since 3.3.0, default: 8)

  # ---------------------------------------------------------------- datafusion (query engine)
  datafusion:
    num_threads: ""                  # --datafusion-num-threads               [env: INFLUXDB3_DATAFUSION_NUM_THREADS]               (since 3.0.0)
    max_parquet_fanout: ""           # --datafusion-max-parquet-fanout        [env: INFLUXDB3_DATAFUSION_MAX_PARQUET_FANOUT]        (since 3.0.0, default: 1000)
    use_cached_parquet_loader: false # --datafusion-use-cached-parquet-loader [env: INFLUXDB3_DATAFUSION_USE_CACHED_PARQUET_LOADER] (since 3.0.0) - SWITCH
    config: ""                       # --datafusion-config                    [env: INFLUXDB3_DATAFUSION_CONFIG]                    (since 3.0.0)

  # ---------------------------------------------------------------- processing engine (plugins)
  processing_engine:
    plugin_dir: ""                   # --plugin-dir                  [env: INFLUXDB3_PLUGIN_DIR]                  (since 3.0.0)
    plugin_repo: ""                  # --plugin-repo                 [env: INFLUXDB3_PLUGIN_REPO]                 (since 3.5.0)
    virtual_env_location: ""         # --virtual-env-location        [env: VIRTUAL_ENV]                          (since 3.0.0)
    package_manager: ""              # --package-manager             [env: INFLUXDB3_PACKAGE_MANAGER]             (since 3.0.0, default: discover)
    restrict_plugin_triggers_to: ""  # --restrict-plugin-triggers-to [env: INFLUXDB3_RESTRICT_PLUGIN_TRIGGERS_TO] (since 3.10.0)

  # ---------------------------------------------------------------- logging
  log:
    filter: "info"         # --log-filter      [env: INFLUXDB3_LOG_FILTER]      (since 3.0.0, default: info)
    destination: "stdout"  # --log-destination [env: INFLUXDB3_LOG_DESTINATION] (since 3.0.0, default: stdout)
    format: "full"         # --log-format      [env: INFLUXDB3_LOG_FORMAT]      (since 3.0.0, default: full)

  # ---------------------------------------------------------------- tracing
  tracing:
    exporter: ""  # --traces-exporter  [env: INFLUXDB3_TRACES_EXPORTER]  (since 3.0.0, default: none)
    jaeger:
      agent_host: ""                 # --traces-exporter-jaeger-agent-host                 (since 3.0.0, default: 0.0.0.0)
      agent_port: ""                 # --traces-exporter-jaeger-agent-port                 (since 3.0.0, default: 6831)
      service_name: ""               # --traces-exporter-jaeger-service-name               (since 3.0.0, default: iox-conductor)
      trace_context_header_name: ""  # --traces-exporter-jaeger-trace-context-header-name  (since 3.0.0, default: uber-trace-id)
      debug_name: ""                 # --traces-jaeger-debug-name                          (since 3.0.0, default: jaeger-debug-id)
      tags: ""                       # --traces-jaeger-tags                                (since 3.0.0)
      max_msgs_per_second: ""        # --traces-jaeger-max-msgs-per-second                 (since 3.0.0, default: 1000)

  # ---------------------------------------------------------------- telemetry
  telemetry:
    disable_upload: false  # --disable-telemetry-upload [env: INFLUXDB3_TELEMETRY_DISABLE_UPLOAD] (since 3.0.0) - SWITCH
    endpoint: ""           # --telemetry-endpoint       [env: INFLUXDB3_TELEMETRY_ENDPOINT]        (since 3.0.0)
```

### `influxdb3_databases`

```yaml
influxdb3_databases:
  host: "http://127.0.0.1:8181"
  token: "{{ operator.token }}"
  databases:
    sensors:
      state: create
    logs:
      state: create
```

## Author and License

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
