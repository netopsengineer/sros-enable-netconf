# sros-enable-netconf
Programatically enable NETCONF and MD-CLI on SROS Devices.

This command line driven utility will programatically connect via an initial SSH session utilizing Netmiko to a far-end remote device.
A pre-compiled list of commands will be deployed to the individual device and enable NETCONF, as well as change from the Classic CLI 
to the new Model Driven CLI.

AFter the configuration changes are completed, the ssh session will be disconnected and a new connection on default NETCONF port 830,
will be established. A configuration backup will then be completed via the NETCONF, get.config and categorized by the system host name.

Although this tool is very useful in a lab environment, it has not been tested in production and it's part of a training excersice. 
This code will be re-constructed to use a list of devices from the NETBOX API.

The tool was built to follow a theoretical issue as part of a blog post:
https://adminsave.wordpress.com/2020/05/18/programatically-enable-netconf-and-md-cli-on-nokia-sros/

## Security and supported setup

Use Python 3.12 or newer (CI exercises 3.12 and 3.14), uv 0.13.4 or newer,
and Poetry 2.5.1. Install uv from its official distribution, then run
`uv tool install poetry==2.5.1 --with poetry-plugin-export==1.10.1` and
`poetry sync`. The committed Poetry lock is the dependency source of truth.
Do not use an outdated system pip to bootstrap downloads; pip must be at least
26.2.2 for the October 2026 CA trust-store update.

SSH connections now reject unknown or changed host keys. Before running against
a device, independently verify its host-key fingerprint with the administrator
and provision the verified key in your user's `~/.ssh/known_hosts`. Do not trust
an unverified `ssh-keyscan` result. NETCONF on a nonstandard port needs the
corresponding `[hostname]:port` entry as well. No automatic key enrollment or
host-key bypass is provided. Existing deployments without verified keys will
fail closed until the operator provisions them.

Tests use mocks only and do not contact hosts or change device configuration.
Run `poetry run pytest` before using this tutorial. No live device compatibility
or deployment is claimed by these offline checks.

The shared NETCONF password default has been removed. Supply NETCONF_PASS through
your existing secure environment or enter it at the hidden prompt. Running the
application provisions remote access and changes router configuration; review
and authorize that operation separately. Dependency updates do not run it.

Provisioning usernames accept letters, digits, underscore, dot, and hyphen.
Passwords accept letters, digits, and _.@!%+=,-; whitespace, quotes, shell/CLI
separators, and control characters are rejected before connecting. Transport
logging is filtered to prevent provisioning commands from reaching application logs.
