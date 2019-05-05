import logging
import os

try:
    import pwd
except ModuleNotFoundError:
    pass

logger = logging.getLogger(__name__)


class Privilege(object):
    __slots__ = []

    _root_user_gid = 0
    _root_user_uid = 0
    _gid_of_user_invoking_sudo = None
    _uid_of_user_invoking_sudo = None

    @classmethod
    def become_privileged_user(cls):
        try:
            os.setegid(cls._root_user_gid)
            os.seteuid(cls._root_user_uid)
        except AttributeError:
            pass

    @classmethod
    def become_unprivileged_user(cls):
        try:
            os.setegid(cls._gid_of_user_invoking_sudo)
            os.seteuid(cls._uid_of_user_invoking_sudo)
        except AttributeError:
            pass

    @classmethod
    def initialize(cls):
        try:
            cls._root_user_gid = os.getgid()
            cls._root_user_uid = os.getuid()

            try:
                username_of_user_invoking_sudo = os.environ['SUDO_USER']
                password_database_entry_for_user_invoking_sudo = pwd.getpwnam(username_of_user_invoking_sudo)

                cls._gid_of_user_invoking_sudo = password_database_entry_for_user_invoking_sudo.pw_gid
                cls._uid_of_user_invoking_sudo = password_database_entry_for_user_invoking_sudo.pw_uid
            except KeyError:
                cls._gid_of_user_invoking_sudo = cls._root_user_gid
                cls._uid_of_user_invoking_sudo = cls._root_user_uid
        except AttributeError:
            pass
