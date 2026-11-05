"""The neutral providers now live in credchain; every old import path still works.

Their behavior is tested in credchain. These tests only pin the import paths
that consumers use, so the move stays invisible to them.
"""

import credchain
import credchain.keyring

import fastmcp_creds
from fastmcp_creds import chain, env, keyring, protocol


def test_package_root_reexports():
    assert fastmcp_creds.CredentialsProvider is credchain.CredentialsProvider
    assert fastmcp_creds.CredentialsProviderChain is credchain.CredentialsProviderChain
    assert (
        fastmcp_creds.EnvironmentCredentialsProvider
        is credchain.EnvironmentCredentialsProvider
    )


def test_module_paths_reexport():
    assert protocol.CredentialsProvider is credchain.CredentialsProvider
    assert chain.CredentialsProviderChain is credchain.CredentialsProviderChain
    assert (
        env.EnvironmentCredentialsProvider is credchain.EnvironmentCredentialsProvider
    )
    assert (
        keyring.KeyringCredentialsProvider
        is credchain.keyring.KeyringCredentialsProvider
    )
    assert keyring.DEFAULT_KEYRING_TIMEOUT == credchain.keyring.DEFAULT_KEYRING_TIMEOUT
