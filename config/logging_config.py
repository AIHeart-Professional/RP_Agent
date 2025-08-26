import logging
import logging.config
import yaml
import os

def setup_logging(default_path='logging.yaml', default_level=logging.INFO):
    """
    Set up logging configuration from a YAML file.
    It constructs an absolute path to the config file, making it independent
    of the current working directory.
    """
    # Get the absolute path to the directory where this config file lives
    config_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(config_dir, default_path)

    if os.path.exists(path):
        try:
            with open(path, 'rt') as f:
                config = yaml.safe_load(f.read())
            
            # Ensure logs directory exists for file handler
            project_root = os.path.dirname(config_dir)
            logs_dir = os.path.join(project_root, 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Update file handler paths to be absolute
            if 'handlers' in config and 'file' in config['handlers']:
                log_file_path = os.path.join(logs_dir, 'app.log')
                config['handlers']['file']['filename'] = log_file_path
            
            # Check if colorlog is available, fallback to simple formatter if not
            try:
                import colorlog
            except ImportError:
                # Replace colored formatter with simple formatter if colorlog not available
                if 'handlers' in config and 'console' in config['handlers']:
                    if config['handlers']['console'].get('formatter') == 'colored':
                        config['handlers']['console']['formatter'] = 'simple'
            
            # Try to configure with YAML first
            try:
                logging.config.dictConfig(config)
                print(f"Successfully loaded logging config from {path}")
            except Exception as yaml_error:
                print(f"YAML config failed: {yaml_error}, falling back to simple config")
                # Fallback to simple but better formatted logging
                logging.basicConfig(
                    level=default_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
        except Exception as e:
            logging.basicConfig(
                level=default_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            logging.warning(f"Error loading logging config from {path}: {e}. Using basic config.")
    else:
        logging.basicConfig(level=default_level)
        logging.warning(f"logging.yaml not found at {path}. Using basic config.")
