import os
import sys
import getpass
import subprocess
import uuid
import configparser
import argparse
from datetime import datetime

######################################################################################## 
# Utility script to Bulk copy from a SQL Server DB into another SQL Server DB using bcp
######################################################################################## 

# Prompt msg, read input and return input entered by the user
# If the input is blank or contains only whitespaces, 
# the default argument is returned
def read_from_input_or_default(msg, default):
  _input = input(msg)
  formatted_input = str(_input).strip()

  if formatted_input == '':
      return default
  else:
      return formatted_input

# Return a generated file name for the output logs file
# The output logs file will be located in a directory 
# called '/logs' under the given baseDir directory
def init_output_logs_file(baseDir):
    output_file_name = datetime.now().strftime("%Y_%m_%d__%H_%M_%S_%f") + ".txt"
    out_dir = os.path.join(baseDir, 'logs')
    output_logs_file_path = os.path.join(out_dir, output_file_name)

    if not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir)
        except:
            print('Unable to create [' + baseDir + '/logs] dir')

    return output_logs_file_path


# Create a temporary directory in the current working directory
# and return the absolute path of this directory
def create_temp_dir():
    dir_name = str(uuid.uuid4())
    dir_path = os.path.join(os.getcwd(), 'out', dir_name)

    try:
        os.makedirs(dir_path)
    except:
        print('Unable to create temporary dir [' + dir_path + ']')

    return dir_path


# Replace \r\n by carriage return
def format_output(output):
    return str(output).replace('\\r\\n', '\r\n')


# Prompt user to enter its credentials and return an array containing authentication arguments
def get_auth_args():
    srcDbUser = read_from_input_or_default('DB user [Windows Authentication]:', '')

    if srcDbUser == '':
        # Windows authentication
        authArgs = ['-T']
    else:
        # Credentials authentication
        srcDbPassword = getpass.getpass('DB password:')
        authArgs = ['-U', srcDbUser, '-P', srcDbPassword]

    return authArgs or []


# Prompt for config and return user inputs
def prompt_for_config():
    print('')
    print('##############################')
    print('# SOURCE DB')
    print('##############################')
    src_db_instance = read_from_input_or_default('SQL server_name\instance [153.89.154.109]:', '153.89.154.109')
    src_db_name = read_from_input_or_default('DB name [csd-tarfac]:', 'csd-tarfac')
    src_auth_args = get_auth_args()

    print('')
    print('')
    print('##############################')
    print('# DESTINATION DB')
    print('##############################')
    dest_db_instance = read_from_input_or_default('SQL server_name\instance [localhost]:', 'localhost')
    dest_db_name = read_from_input_or_default('DB name [csd-tarfac]:', 'csd-tarfac')
    dest_auth_args = get_auth_args()

    return src_db_instance, src_db_name, src_auth_args, dest_db_instance, dest_db_name, dest_auth_args


# Parse command args
def parse_args():
    parser = argparse.ArgumentParser(description='Bulk export-import utility')
    parser.add_argument('-c', '--config', dest='configFilePath',
                        help='Path to config file')

    parser.add_argument('-t', '--tables', dest='tables', nargs='+',
                        help='Database tables to bulk export-import: --c <TABLE_1> <TABLE_2> ... <TABLE_N>')

    parser.add_argument('-y', '--confirm-yes', dest='autoConfirm', action='store_true', default=False,
                        help='If this arg is present, does not prompt for confirmation')

    return parser.parse_args()


# Prompt for user confirmation. 
# Returns True if user enters 'y', False if user enters 'n'
def prompt_for_confirm():
    choice = ''

    while True:
        choice = input("Would you like to apply this bulk? y (yes) | n (no): ")

        if choice.lower() in ('y', 'yes'):
            return True
        elif choice.lower() in ('n', 'no'):
            return False


# Read from config file and return config values
def read_from_config_file(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    srcDbInstance = config.get('Database', 'database.source.instance')
    src_db_name = config.get('Database', 'database.source.dbname')
    src_windows_auth = config.get('Database', 'database.source.windowsauth')

    if src_windows_auth == 'True':
        src_auth_args = ['-T']
    else:
        src_user = config.get('Database', 'database.source.user')
        src_password = config.get('Database', 'database.source.password')
        src_auth_args = ['-U', src_user, '-P', src_password]

    dest_db_instance = config.get('Database', 'database.destination.instance')
    dest_db_name = config.get('Database', 'database.destination.dbname')
    dest_windows_auth = config.get('Database', 'database.destination.windowsauth')

    if dest_windows_auth == 'True':
        dest_auth_args = ['-T']
    else:
        dest_user = config.get('Database', 'database.destination.user')
        dest_password = config.get('Database', 'database.destination.password')
        dest_auth_args = ['-U', dest_user, '-P', dest_password]

    tables = []
    if config.has_option('Bulk', 'bulk.tables'):
        tables = config.get('Bulk', 'bulk.tables')
        tables = [i.strip() for i in tables.split(',')]
    
    return srcDbInstance, src_db_name, src_auth_args, dest_db_instance, dest_db_name, dest_auth_args, tables


def main():
    # Parce CLI arguments
    args = parse_args()

    tables = []

    # Get config from given file or prompt if no file given
    if args.configFilePath:
        if not os.path.exists(args.configFilePath):
            raise Exception('Unknown file', args.configFilePath)

        src_db_instance, src_db_name, src_auth_args, dest_db_instance, dest_db_name, dest_auth_args, tables = read_from_config_file(args.configFilePath)
    else:
        src_db_instance, src_db_name, src_auth_args, dest_db_instance, dest_db_name, dest_auth_args = prompt_for_config()

    # If tables are given in CLI args, this overrides the tables in config file
    if args.tables:
        tables = args.tables

    # Remove duplicates from tables list
    #tables = list(set(tables))

    if len(tables) == 0:
        print('No config found for tables. Please specify tables in config file or using --tables CLI option')
        exit(1)

    print('')
    print('##############################')
    print('Importing data')
    print('FROM: ' + src_db_instance + ' (DB: ' + src_db_name + ') ' + ('(Windows authentication)' if ('-T' in src_auth_args) else ('(user: ' + src_auth_args[1] + ')')))
    print('INTO: ' + dest_db_instance + ' (DB: ' + dest_db_name + ') ' + ('(Windows authentication)' if ('-T' in dest_auth_args) else ('(user: ' + dest_auth_args[1] + ')')))
    print('')
    print('TABLES: \n- ' + (', '.join(tables)).replace(', ', '\n- '))
    print('##############################')
    print('')
    print('')

    if not args.autoConfirm:
        if not prompt_for_confirm():
            exit()

    start_time = datetime.now()
    temporary_dir_path = create_temp_dir()
    output_logs_file_path = init_output_logs_file(temporary_dir_path)

    with open(output_logs_file_path, "w") as f:
        for table_name in tables:
            try:
                print('Copying data from table [' + table_name + '] ...')

                table_data_file = os.path.join(temporary_dir_path, (table_name + '.txt'))

                # BCP out
                output = subprocess.check_output(['bcp', table_name, 'out', table_data_file, '-S', src_db_instance, '-d', src_db_name, '-c', '-C', '65001'] + src_auth_args)
                f.write(format_output(output))
                
                # BCP in
                output = subprocess.check_output(['bcp', table_name, 'in', table_data_file, '-q', '-E' , '-S', dest_db_instance, '-d', dest_db_name, '-c', '-C', '65001'] + dest_auth_args)
                f.write(format_output(output))

                # Remove temporary file
                os.remove(table_data_file)

                print('Table [' + table_name + '] successfully copied!')
                print('')

            except subprocess.CalledProcessError as exc:
                err_msg = ' [ERROR]: ', exc.returncode, exc.output
                formatted_output = format_output(err_msg)
                f.write(formatted_output)
                print(formatted_output)

                if os.path.exists(table_data_file):
                    os.remove(table_data_file)

    # Delete temporary directory
    #if os.path.isdir(temporary_dir_path):
    #    os.rmdir(temporary_dir_path)
    
    # Affichage du temps d'exécution
    end_time = datetime.now()
    duration = divmod((end_time - start_time).seconds, 60)
    print('')
    print('##############################')
    print('Duration: ' + str(duration[0]) + ' min ' + str(duration[1]) + ' sec')
    print('##############################')
    print('')

    input("Press Enter to continue...")

main()