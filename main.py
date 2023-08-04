import openpyxl
from UliPlot.XLSX import auto_adjust_xlsx_column_width as adjust
import pandas as pd
from datetime import datetime
from string import Template
import requests
import logging
import sys


def initialize_logger():
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO,
                        filename=f'cleanup_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.log',
                        filemode='a')
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    return logger


def get_nr_account_ids(url, headers):

    # response['data']['actor']['accounts'] (list of accounts)
    # account keys: 'id', 'name'
    nr_gql_accounts_query = Template("""
    {
      actor {
        accounts {
          id
          name
        }
      }
    }
    """)

    accounts_query_fmtd = nr_gql_accounts_query.substitute({})
    nr_response = requests.post(url,
                                headers=headers,
                                json={'query': accounts_query_fmtd}).json()
    # logger.info(f'New Relic API response:\n{type(nr_response)}')

    return nr_response


def generate_conditions_report(client_name, account_id, logger):
    logger.info(f'Processing conditions for {client_name}...')
    success = False

    # create a dataframe with column headings
    client_df = pd.DataFrame(columns=['Client', 'Condition Type', 'Condition Name', 'Query',
                                      'Description', 'Condition ID', 'Policy ID'])

    # TODO: REST API call for infrastructure alerts

    # query API and put all conditions for client into a dataframe
    nr_endpoint = 'https://api.newrelic.com/graphql'
    nr_headers = {
        'Content-Type': 'application/json',
        'API-Key': 'NRAK-7DVT82DILPFIAXSZZ6CLPKYB8YU',
    }
    nr_gql_condition_query = Template("""
    {
      actor {
        account(id: $account_id) {
          alerts {
            nrqlConditionsSearch {
              nrqlConditions {
                id
                name
                nrql {
                  query
                }
                description
                policyId
              }
            }
          }
        }
      }
    }
    """)

    condition_query_fmtd = nr_gql_condition_query.substitute({'account_id': account_id})
    nrql_response = requests.post(nr_endpoint,
                                  headers=nr_headers,
                                  json={'query': condition_query_fmtd}).json()
    # logger.debug(f'New Relic API response:\n{nr_response}')

    try:
        conditions_list = nrql_response['data']['actor']['account']['alerts']['nrqlConditionsSearch']['nrqlConditions']

        logger.info(f'{len(conditions_list)} NRQL conditions found:')

        # evaluate destinations
        if conditions_list:
            for condition in conditions_list:
                condition_name = condition['name']
                condition_query = condition['nrql']['query']
                condition_description = condition['description']
                condition_id = condition['id']
                policy_id = condition['policyId']

                logger.info(f'   Condition: {condition_name}')
                # keep_workflow, disable_workflow = do_keep_disable_workflow(workflow, logger)
                # logger.info(f'         Keep workflow: {keep_workflow}')
                # logger.info(f'         Disable workflow: {disable_workflow}')

                # 'Client', 'Condition Type', 'Condition Name', 'Query', 'Description', 'Condition ID', 'Policy ID'
                row = [client_name, condition_name, condition_query, condition_description,
                       condition_id, policy_id]
                # logger.info(f'            Row: {row}')
                # logger.info(f'            Row length: {len(row)}')

                client_df.loc[len(client_df)] = row

            logger.info(client_df.head(2))

            # write client dataframe as sheet to 'Conditions Report.xlsx' with sheet_name=client_name
            try:
                with pd.ExcelWriter('Conditions Report.xlsx', mode='a', if_sheet_exists='replace') as writer:
                    client_df.to_excel(writer, sheet_name=client_name, index=False)
                    adjust(client_df, writer, sheet_name=client_name, margin=3, index=False)
            except FileNotFoundError:
                with pd.ExcelWriter('Conditions Report.xlsx') as writer:
                    client_df.to_excel(writer, sheet_name=client_name, index=False)
                    adjust(client_df, writer, sheet_name=client_name, margin=3, index=False)

            success = True

        # handle clients with no workflows
        else:
            logger.info(f'   {client_name} does not have any NRQL conditions; skipping client.\n')

    except TypeError:
        logger.info(f'   New Relic returned an unusual response for {client_name}; skipping client. \n')

    return success, client_df


def main():
    logger = initialize_logger()
    all_dfs = []

    url = 'https://api.newrelic.com/graphql'
    headers = {
        'Content-Type': 'application/json',
        'API-Key': 'NRAK-7DVT82DILPFIAXSZZ6CLPKYB8YU',
    }

    accounts = get_nr_account_ids(url, headers)

    # Testing
    # test_account = [{
    #       "id": 2739507,
    #       "name": "2W-MCS-SCCA"
    # }]
    # for account in test_account:

    for account in accounts['data']['actor']['accounts']:
        account_id = account['id']
        client_name = account['name']

        logger.info(f'{client_name}: {account_id}')

        client_name_sliced = client_name[:30]

        success, client_df = generate_conditions_report(client_name_sliced, account_id, logger)

        if success:
            logger.info(f'\n{client_name} processed successfully.\n')
            all_dfs.append(client_df)

    all_conditions = pd.concat(all_dfs)

    with pd.ExcelWriter('Conditions Report.xlsx', mode='a', if_sheet_exists='replace') as writer:
        all_conditions.to_excel(writer, sheet_name='All Conditions', index=False)
        adjust(all_conditions, writer, sheet_name='All Conditions', margin=3, index=False)

    workbook = openpyxl.load_workbook('Conditions Report.xlsx')
    workbook._sheets.sort(key=lambda ws: ws.title)
    workbook.move_sheet('All Conditions', 0 - workbook.sheetnames.index('All Conditions'))
    workbook.save('Conditions Report sorted.xlsx')


main()
