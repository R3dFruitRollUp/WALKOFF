import json
import sys
import os
from six.moves import configparser
from six.moves import input
import tarfile
import zipfile

from walkoff.config import Config


def set_walkoff_external():
    default = os.getcwd()
    sys.stdout.write(" * Enter a directory to install WALKOFF apps, interfaces, and data to (default: {}): "
                     .format(default))
    Config.WALKOFF_EXTERNAL_PATH = input()

    if Config.WALKOFF_EXTERNAL_PATH == '':
        Config.WALKOFF_EXTERNAL_PATH = default

    if not os.path.isdir(Config.WALKOFF_EXTERNAL_PATH):
        try:
            print("Creating {}".format(Config.WALKOFF_EXTERNAL_PATH))
            os.makedirs(Config.WALKOFF_EXTERNAL_PATH)
        except OSError as e:
            print("Specified directory could not be created: {}".format(e))
            sys.exit(1)

    arch_path = os.path.join(Config.WALKOFF_INTERNAL_PATH, "walkoff_external")

    if os.name == 'posix':
        arch_path += ".tar.gz"
        archf = tarfile.open(arch_path)

    elif os.name == 'nt':
        arch_path += ".zip"
        archf = zipfile.ZipFile(arch_path)

    archf.extractall(Config.WALKOFF_EXTERNAL_PATH)

    Config.WALKOFF_EXTERNAL_PATH = os.path.join(Config.WALKOFF_EXTERNAL_PATH, "walkoff_external")

    Config.DATA_PATH = os.path.join(Config.WALKOFF_EXTERNAL_PATH, 'data')
    Config.APPS_PATH = os.path.join(Config.WALKOFF_EXTERNAL_PATH, 'apps')
    Config.CACHE_PATH = os.path.join(Config.DATA_PATH, 'cache')
    Config.CASE_DB_PATH = os.path.join(Config.DATA_PATH, 'events.db')
    Config.CACHE = {"type": "disk", "directory": Config.CACHE_PATH, "shards": 8, "timeout": 0.01, "retry": True}
    Config.DB_PATH = os.path.join(Config.DATA_PATH, 'walkoff.db')
    Config.DEFAULT_APPDEVICE_EXPORT_PATH = os.path.join(Config.DATA_PATH, 'appdevice.json')
    Config.DEFAULT_CASE_EXPORT_PATH = os.path.join(Config.DATA_PATH, 'cases.json')
    Config.EXECUTION_DB_PATH = os.path.join(Config.DATA_PATH, 'execution.db')
    Config.INTERFACES_PATH = os.path.join(Config.WALKOFF_EXTERNAL_PATH, 'interfaces')
    Config.LOGGING_CONFIG_PATH = os.path.join(Config.DATA_PATH, 'log', 'logging.json')

    Config.WALKOFF_SCHEMA_PATH = os.path.join(Config.DATA_PATH, 'walkoff_schema.json')

    Config.KEYS_PATH = os.path.join(Config.WALKOFF_EXTERNAL_PATH, '.certificates')
    Config.CERTIFICATE_PATH = os.path.join(Config.KEYS_PATH, 'walkoff.crt')
    Config.PRIVATE_KEY_PATH = os.path.join(Config.KEYS_PATH, 'walkoff.key')
    Config.ZMQ_PRIVATE_KEYS_PATH = os.path.join(Config.KEYS_PATH, 'private_keys')
    Config.ZMQ_PUBLIC_KEYS_PATH = os.path.join(Config.KEYS_PATH, 'public_keys')

    Config.write_values_to_file()


def set_alembic_paths():
    Config.load_config()
    config = configparser.ConfigParser()
    alembic_ini = os.path.join(Config.WALKOFF_INTERNAL_PATH, 'scripts', 'migrations', 'alembic.ini')
    with open(alembic_ini, "r") as f:
        config.readfp(f)

    config.set("walkoff", "sqlalchemy.url", "sqlite:///{}".format(Config.DB_PATH))
    config.set("events", "sqlalchemy.url", "sqlite:///{}".format(Config.CASE_DB_PATH))
    config.set("execution", "sqlalchemy.url", "sqlite:///{}".format(Config.EXECUTION_DB_PATH))

    with open(alembic_ini, "w") as f:
        config.write(f)


def set_logging_path():
    Config.load_config()
    logging_json = Config.LOGGING_CONFIG_PATH
    log_log = os.path.join(Config.DATA_PATH, 'log', 'log.log')
    with open(logging_json, "r") as f:
        o = json.load(f)
        o["handlers"]["file_handler"]["filename"] = log_log

    with open(logging_json, "w") as f:
        json.dump(o, f, indent=2, sort_keys=True)


def main():
    set_walkoff_external()
    set_alembic_paths()
    set_logging_path()


if __name__ == '__main__':
    main()