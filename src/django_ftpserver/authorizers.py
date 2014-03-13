import os
import pwd

from django.contrib.auth import authenticate
from pyftpdlib.authorizers import AuthenticationFailed

from . import models


class FTPAccountAuthorizer(object):
    """Authorizer class by django authentication.
    """
    model = models.FTPUserAccount

    def __init__(self, file_access_user=None):
        self.file_access_user = file_access_user
        self.gid = os.getgid()
        self.uid = os.getuid()

    def has_user(self, username):
        """return True if exists user.
        """
        return self.model.objects.filter(user__username=username).exists()

    def get_account(self, username):
        """return user by username.
        """
        try:
            account = self.model.objects.get(user__username=username)
        except self.model.DoesNotExist:
            return None
        return account

    def validate_authentication(self, username, password, handler):
        user = authenticate(username=username, password=password)
        account = self.get_account(username)
        if not (user and account):
            raise AuthenticationFailed("Authentication failed.")

    def get_home_dir(self, username):
        account = self.get_account(username)
        if not account:
            return ''
        return account.get_home_dir()

    def get_msg_login(self, username):
        """message for welcome.
        """
        account = self.get_account(username)
        if account:
            account.update_last_login()
            account.save()
        return 'welcome.'

    def get_msg_quit(self, username):
        return 'good bye.'

    def has_perm(self, username, perm, path=None):
        account = self.get_account(username)
        return account and account.has_perm(perm, path)

    def get_perms(self, username):
        account = self.get_account(username)
        return account and account.get_perms()

    def impersonate_user(self, username, password):
        if self.file_access_user:
            uid = pwd.getpwnam(self.file_access_user).pw_uid
            gid = pwd.getpwnam(self.file_access_user).pw_gid
            os.setegid(gid)
            os.seteuid(uid)

    def terminate_impersonation(self, username):
        if self.file_access_user:
            os.setegid(self.gid)
            os.seteuid(self.uid)
