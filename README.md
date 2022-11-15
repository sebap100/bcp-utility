# bcp-utility
Utility to easily copy data between two SQL Server instances using bcp

## Requirements
- python >3
- SQL Server >2016
- bcp >15

## Usage
```
usage: bcp_utility.py [-h] [-c CONFIGFILEPATH] [-t TABLES [TABLES ...]] [-y]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILEPATH, --config CONFIGFILEPATH
                        Path to config file
  -t TABLES [TABLES ...], --tables TABLES [TABLES ...]
                        Database tables to bulk export-import: --c <TABLE_1> <TABLE_2> ... <TABLE_N>
  -y, --confirm-yes     If this arg is present, does not prompt for confirmation
```

## Config file example
```properties
[Database]
database.source.instance=
database.source.dbname=
database.source.windowsauth=False
database.source.user=my-user
database.source.password=my-password

database.destination.instance=
database.destination.dbname=
database.destination.windowsauth=True
database.destination.user=
database.destination.password=

[Bulk]
bulk.tables=TABLE_1, TABLE_2
```

## Run
```batch
python bcp_utility.py -c <path_to_config_file>
```
