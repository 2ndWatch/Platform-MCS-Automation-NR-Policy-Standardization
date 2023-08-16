import requests
import pandas as pd
import json
from time import sleep


def get_infrastructure_conditions():
    with open('keys.json') as k:
        k_txt = k.read()
    keys_dict = json.loads(k_txt)

    policies_url = 'https://api.newrelic.com/v2/alerts_policies.json'

    policies_df = pd.DataFrame(columns=['Client', 'Condition Type', 'Policy Name', 'Condition Name', 'Priority',
                                        'Operator', 'Threshold', 'Duration', 'Query/Threshold', 'Description',
                                        'Condition ID', 'Policy ID'])

    for client, key in keys_dict.items():
        print(f'Client: {client}')

        policies_headers = {
            "X-Api-Key": key
        }

        policies_response = requests.get(policies_url, headers=policies_headers)
        # print(policies_response.json())

        policy_ids = []
        policy_names = []

        try:
            for policy in policies_response.json()['policies']:
                if 'Standard' in policy['name']:
                    policy_ids.append(policy['id'])
                    policy_names.append(policy['name'])

            # print(policies_list)

            condition_url = 'https://infra-api.newrelic.com/v2/alerts/conditions'
            condition_headers = {
                "Api-Key": key
            }

            for i in range(len(policy_ids)):
                params = {
                    "policy_id": policy_ids[i]
                }

                response = requests.get(condition_url, headers=condition_headers, params=params)

                # print(response.json())

                try:
                    if response.json()['data']:
                        for data in response.json()['data']:
                            print(f'   Policy {policy_ids[i]}: {data}')

                            condition_type = 'infra'
                            condition_name = data['name']
                            condition_threshold = data['critical_threshold']
                            condition_description = ''
                            threshold = '-'
                            threshold_duration = '-'
                            try:
                                threshold = condition_threshold['value']
                            except KeyError:
                                print('      No threshold value given.')
                            try:
                                threshold_duration = condition_threshold['duration_minutes']
                            except KeyError:
                                print('      No threshold duration given.')
                            try:
                                condition_description = f'{data["event_type"]} {data["select_value"]}'
                            except KeyError:
                                print(f'      No event_type for {condition_name}')
                            condition_id = data['id']

                            row = [client, condition_type, policy_names[i], condition_name, '-', '-', threshold,
                                   threshold_duration, condition_threshold, condition_description, condition_id,
                                   policy_ids[i]]

                            policies_df.loc[len(policies_df)] = row
                except json.decoder.JSONDecodeError:
                    continue
        except KeyError:
            print(f'   No infrastructure polices for {client}')

        print(f'\n{policies_df.tail(5)}')

        print(f'\n{client} processed successfully.')

        time = 11
        for i in range(10):
            sleep(1)
            time -= 1
            print(f'   Continuing in {time}')
        print('\n')

    return policies_df
