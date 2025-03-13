from setuptools import setup, find_packages

setup(
    name='ckanext-sso_new_user_handler',
    version='0.1.0',
    description='CKAN extension to automatically create users from SSO and add them to an organization',
    long_description='''
        A CKAN extension that automatically provisions user accounts when users authenticate via SSO (Azure AD).
    ''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 3',
    ],
    keywords='CKAN SSO SAML Azure',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/your-org/ckanext-sso_new_user_handler',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # dependencies
    ],
    entry_points='''
        [ckan.plugins]
        sso_new_user_handler=ckanext.sso_new_user_handler.plugin:SsoNewUserHandlerPlugin
    ''',
) 