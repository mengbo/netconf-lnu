from .braslogger import BRASLogger
import argparse
import importlib.util


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', dest='config_file',
                        default='/etc/netconf-lnu/config.ini',
                        help='Path to the configuration file.')
    parser.add_argument('-t', '--test', dest='test_function',
                        help='Run the test function.')
    args = parser.parse_args()

    config_file_path = args.config_file
    bras_logger = BRASLogger(config_file_path)

    test_function_name = args.test_function
    if test_function_name:
        try:
            test_module = importlib.import_module('.mytest', package=__package__)
            test_function = getattr(test_module, test_function_name)
            test_function(bras_logger)
        except (ImportError, AttributeError):
            print('Unknow function!!!')
    else:
        bras_logger.write_syslog()


if __name__ == "__main__":
    main()
