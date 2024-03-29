from methods.basetype import MethodBaseType
import delegator
import paramiko
import logging
import IPy


class Command(MethodBaseType):
    @staticmethod
    def run(config: dict = None) -> str:
        if not config:
            return ''
        if 'cmd' in config:
            command = config['cmd']
        else:
            logging.warning("无命令")
            return ''
        if 'ssh' in config and config['ssh']:
            try:
                if 'timeout' not in config['ssh']:
                    config['ssh']['timeout'] = 10
                if 'auth_timeout' not in config['ssh']:
                    config['ssh']['auth_timeout'] = 5
                if 'allow_agent' not in config['ssh']:
                    config['ssh']['allow_agent'] = False
                if 'look_for_keys' not in config['ssh']:
                    config['ssh']['look_for_keys'] = True
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(**config['ssh'])
                stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
                logging.warning(stderr)
                out = stdout.read().decode().strip().replace('\r\n', '\n')
                ssh.close()
            except:
                logging.warning("SSH 连接时出错")
                return ''
        else:
            out = delegator.run(command).out.strip()
        return out

    @staticmethod
    def getip(version: int = 4, interface: str = "", config: dict = None) -> list:
        out = Command.run(config)
        try:
            if out and IPy.IP(out).version() == version:
                return [out]
            else:
                raise
        except:
            return []
