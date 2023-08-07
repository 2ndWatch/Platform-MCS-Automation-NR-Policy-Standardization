import requests
import pandas as pd
import json


def get_infrastructure_conditions():
    with open('keys.json') as k:
        k_txt = k.read()
    keys_dict = json.loads(k_txt)

    policies_url = 'https://api.newrelic.com/v2/alerts_policies.json'

    policies_df = pd.DataFrame(columns=['Client', 'Condition Type', 'Policy Name', 'Condition Name', 'Query/Threshold',
                                        'Description', 'Condition ID', 'Policy ID'])

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

                if response.json()['data']:
                    for data in response.json()['data']:
                        print(f'   Policy {policy_ids[i]}: {data}')

                        condition_type = 'infra'
                        condition_name = data['name']
                        condition_threshold = data['critical_threshold']
                        condition_description = ''
                        try:
                            condition_description = f'{data["event_type"]} {data["select_value"]}'
                        except KeyError:
                            print(f'      No event_type for {condition_name}')
                        condition_id = data['id']

                        row = [client, condition_type, policy_names[i], condition_name, condition_threshold,
                               condition_description, condition_id, policy_ids[i]]

                        policies_df.loc[len(policies_df)] = row
        except KeyError:
            print(f'   No infrastructure polices for {client}')

        print(policies_df.tail(5))

    return policies_df
