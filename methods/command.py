from methods.base import Method
import delegator
import paramiko
import logging


class Command(Method):
    @staticmethod
    def exec(command: str, ssh: dict = None) -> str:
        try:
            if ssh:
                ssh.setdefault('timeout', 10)
                ssh.setdefault('auth_timeout', 5)
                ssh.setdefault('allow_agent', False)
                ssh.setdefault('look_for_keys', True)
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(**ssh)
                stdin, stdout, stderr = client.exec_command(command, timeout=ssh['timeout'])
                logging.warning(stderr)
                out = stdout.read().decode().strip().replace('\r\n', '\n')
                client.close()
            else:
                out = delegator.run(command).out.strip()
        except Exception as e:
            logging.error(f"Run command error: {e}")
            return ''
        return out

    @staticmethod
    def run(command: str, ssh: dict = None) -> dict[str, dict[str, str]]:
        ip = Command.exec(command, ssh)
        return {ip: {}} if ip else {}
