import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import logging
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger(__name__)

class SsoNewUserHandlerPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthenticator, inherit=True)
    
    # Configuration defaults
    DEFAULT_ORG = 'scion'
    DEFAULT_ROLE = 'member'
    
    def identify(self):
        # Let the normal authentication process happen first
        
        # Check if we have a SAML identity but no CKAN user
        if toolkit.request.environ.get('REMOTE_USER') and not toolkit.c.user:
            try:
                # Extract user details from SAML assertion
                saml_info = toolkit.request.environ.get('saml_info', {})
                email = self._get_saml_attribute(saml_info, 'email')
                firstname = self._get_saml_attribute(saml_info, 'firstname')
                lastname = self._get_saml_attribute(saml_info, 'lastname')
                
                if email:
                    # Create user and add to organization
                    user_dict = self._create_user_from_saml(email, firstname, lastname)
                    if user_dict:
                        self._add_user_to_organization(user_dict['id'], self.get_default_org(), self.get_default_role())
                        log.info(f"Auto-created user {user_dict['name']} and added to {self.get_default_org()} organization")
                        
                        # Send email notification about new user
                        self._send_new_user_notification(user_dict, firstname, lastname, email)
            except Exception as e:
                # Log error but don't disrupt UI
                log.error(f"Failed to auto-create user: {str(e)}")
                
        # Continue normal flow
        return
    
    def _get_saml_attribute(self, saml_info, attribute_name):
        """Extract attribute from SAML info"""
        attributes = saml_info.get('attributes', {})
        
        # Map our attribute names to what comes from Azure AD
        attribute_map = {
            'email': 'emailAddress',
            'firstname': 'givenName',
            'lastname': 'surname'
        }
        
        saml_attr = attribute_map.get(attribute_name, attribute_name)
        values = attributes.get(saml_attr, [])
        return values[0] if values else None
    
    def _create_user_from_saml(self, email, firstname, lastname):
        """Create a new CKAN user from SAML attributes"""
        try:
            # Check if user with this email already exists
            try:
                existing_user = toolkit.get_action('user_show')(
                    {'ignore_auth': True}, {'email': email}
                )
                log.info(f"User with email {email} already exists")
                return existing_user
            except logic.NotFound:
                pass  # User doesn't exist, continue with creation
            
            # Generate a username from email (before the @)
            username = email.split('@')[0].lower()
            
            # Handle username conflicts by adding a suffix if needed
            username = self._ensure_unique_username(username)
            
            # Create the user
            user_dict = {
                'email': email,
                'name': username,
                'password': self._generate_password(),  # Random password since they'll use SSO
                'fullname': f"{firstname} {lastname}" if firstname and lastname else email,
                'state': 'active'  # Automatically activate the account
            }
            
            # Create user with sysadmin privileges to bypass authorization
            context = {'ignore_auth': True, 'model': toolkit.model}
            user_dict = toolkit.get_action('user_create')(context, user_dict)
            return user_dict
            
        except Exception as e:
            log.error(f"Error creating user: {str(e)}")
            return None
    
    def _ensure_unique_username(self, username_base):
        """Make sure username is unique by adding a suffix if needed"""
        username = username_base
        suffix = 1
        
        while True:
            try:
                toolkit.get_action('user_show')({'ignore_auth': True}, {'id': username})
                # If we get here, user exists, try next suffix
                username = f"{username_base}{suffix}"
                suffix += 1
            except logic.NotFound:
                # Username doesn't exist, we can use it
                return username
    
    def _add_user_to_organization(self, user_id, org_name, role):
        """Add the user to the specified organization with the given role"""
        try:
            # Check if organization exists
            try:
                org = toolkit.get_action('organization_show')(
                    {'ignore_auth': True}, {'id': org_name}
                )
            except logic.NotFound:
                log.error(f"Organization {org_name} not found")
                return
            
            # Add user to organization
            member_dict = {
                'id': org['id'],
                'username': user_id,
                'role': role
            }
            
            toolkit.get_action('organization_member_create')(
                {'ignore_auth': True}, member_dict
            )
            
        except Exception as e:
            log.error(f"Error adding user to organization: {str(e)}")
    
    def _generate_password(self):
        """Generate a random password for the user (they'll use SSO anyway)"""
        return str(uuid.uuid4())
    
    def _send_new_user_notification(self, user_dict, firstname, lastname, email):
        """Send email notification about new user creation"""
        try:
            # Get email settings from CKAN config
            smtp_server = toolkit.config.get('smtp.server', '')
            smtp_port = int(toolkit.config.get('smtp.port', 25))
            smtp_starttls = toolkit.config.get('smtp.starttls', 'False').lower() == 'true'
            smtp_user = toolkit.config.get('smtp.user', '')
            smtp_password = toolkit.config.get('smtp.password', '')
            mail_from = toolkit.config.get('smtp.mail_from', '')
            
            # Get notification recipients from config (comma-separated list)
            admin_emails = toolkit.config.get('ckanext.sso_new_user_handler.admin_emails', '')
            if not admin_emails or not smtp_server or not mail_from:
                log.warning("Email notification not sent: SMTP settings or admin emails not configured")
                return
                
            recipients = [email.strip() for email in admin_emails.split(',')]
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = mail_from
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = 'New CKAN User Created via SSO'
            
            # Email body
            body = f"""
A new user has been automatically created in CKAN via SSO:

Username: {user_dict['name']}
Full Name: {firstname} {lastname if lastname else ''}
Email: {email}
Organization: {self.get_default_org()}
Role: {self.get_default_role()}

This user was created automatically by the SSO New User Handler extension.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_starttls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
                
            log.info(f"Sent new user notification email for {user_dict['name']}")
            
        except Exception as e:
            log.error(f"Failed to send email notification: {str(e)}")

# Allow configuration of the org and role 
    def get_default_org(self):
        return toolkit.config.get('ckanext.sso_new_user_handler.default_org', 'scion')

    def get_default_role(self):
        return toolkit.config.get('ckanext.sso_new_user_handler.default_role', 'member')