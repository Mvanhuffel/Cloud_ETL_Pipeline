import pandas as pd
import yaml
import logging
from sqlalchemy import create_engine
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    logging.info("Configuration file loaded successfully.")
    return config

def extract_data_from_sheets(service, spreadsheet_id, range_name='Sheet1'):
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        logging.info('No data found in the sheet.')
        return pd.DataFrame()
    else:
        df = pd.DataFrame(values[1:], columns=values[0])
        logging.info("Successfully extracted data from Google Sheets.")
        return df

def insert_data_to_db(dataframe, engine, schema, table_name):
    # Convert DataFrame column names to lowercase to match the database column names
    dataframe.columns = [col.lower() for col in dataframe.columns]
    dataframe.to_sql(table_name, engine, schema=schema, if_exists='append', index=False)
    logging.info(f"Data successfully loaded into {schema}.{table_name} table.")

if __name__ == "__main__":
    config = load_config('config.yaml')

    logging.basicConfig(filename=config['log_file_path'], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        creds = Credentials.from_service_account_file(config['service_account_file'])
        service = build('sheets', 'v4', credentials=creds)
        logging.info("Successfully connected to Google Sheets Service.")

        spreadsheet_id = config['file_id']
        data = extract_data_from_sheets(service, spreadsheet_id)

        # Data transformation logic here (if needed)

        engine = create_engine(f"postgresql://{config['db_username']}:{config['db_password']}@{config['db_host']}:{config['db_port']}/{config['db_name']}")
        logging.info("Successfully connected to ElephantSQL database.")

        insert_data_to_db(data, engine, config['schema_name'], config['staging_table_name'])

    except Exception as e:
        logging.error(f"Error in ETL process: {e}")



