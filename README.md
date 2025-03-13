# CKAN SSO New User Handler

A CKAN extension that automatically provisions user accounts when users authenticate via SSO (Azure AD).

## Overview

This extension solves the common CKAN SSO workflow issue where users can authenticate via SSO but don't automatically get CKAN accounts created. With this extension:

1. When a user authenticates via SSO for the first time, a CKAN account is automatically created
2. The user is automatically added to the "Scion" organization with "Member" role
3. The user can immediately start using CKAN without admin intervention

## Requirements

- CKAN 2.9 or later
- ckanext-saml2auth or similar SSO extension

## Installation

1. Activate your CKAN virtual environment:
   ```
   . /usr/lib/ckan/default/bin/activate
   ```

2. Install the extension:
   ```
   cd /usr/lib/ckan/default/src/
   git clone https://github.com/your-org/ckanext-sso_new_user_handler.git
   cd ckanext-sso_new_user_handler
   pip install -e .
   ```

3. Add the plugin to your CKAN configuration file:
   ```
   ckan.plugins = ... sso_new_user_handler
   ```

4. Restart CKAN:
   ```
   sudo service apache2 restart
   ```

## Configuration

The plugin uses these default settings:
- Default organization: "scion"
- Default role: "member"

These can be modified in the plugin.py file if needed.

## How It Works

The extension:
1. Hooks into CKAN's authentication process
2. When a user authenticates via SSO but doesn't have a CKAN account
3. Creates a user account automatically using information from the SAML assertion
4. Adds the user to the configured organization
5. Allows the user to continue their session without interruption

## Troubleshooting

Check the CKAN logs for any errors related to user creation or organization assignment.

## License

[License information]

## Credits

Developed by [Your Organization]
