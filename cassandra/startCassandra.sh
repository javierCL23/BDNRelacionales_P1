#!/bin/bash

podman network create cassandra-net
podman run -i --rm --name cassandra -p 9042:9042 -e CASSANDRA_START_RPC=true --network cassandra-net cassandra
