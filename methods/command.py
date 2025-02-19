from methods.basetype import MethodBaseType
import delegator
import paramiko
import logging
import IPy


class Command(MethodBaseType):
    @staticmethod
    def run(command: str, ssh: dict = None) -> str:
        if ssh:
            try:
                ssh.setdefault('timeout', 10)
                ssh.setdefault('auth_timeout', 5)
                ssh.setdefault('allow_agent', False)
                ssh.setdefault('look_for_keys', True)
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(**ssh)
                stdin, stdout, stderr = client.exec_command(command, timeout=10)
                logging.warning(stderr)
                out = stdout.read().decode().strip().replace('\r\n', '\n')
                client.close()
            except:
                logging.warning("SSH 连接时出错")
                return ''
        else:
            out = delegator.run(command).out.strip()
        return out

    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        out = Command.run(**kwargs)
        try:
            if out and IPy.IP(out).version() == version:
                return [out]
            else:
                raise
        except:
            return []
