#!/usr/bin/env python

import argparse
import boto3
import json

SECURITY_GROUP_NAME = "test-luster-inbound"
VPC_ID = "vpc-f6570b8d"




def sg_exists():
    exists = get_sg_id() is not None
    return exists


def get_sg_id():
    sg = get_sg()
    if sg is None:
        return sg
    return sg['GroupId']


def get_sg():
    """Returns None if sg doesn't exist. Can be used to check for existance"""
    client = boto3.client('ec2')
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_security_groups
    response = client.describe_security_groups(
            Filters=[
                {
                    'Name': 'group-name',
                    'Values': [
                        SECURITY_GROUP_NAME,
                    ]
                },
            ],
    )
    assert not len(response['SecurityGroups']) > 1, "There should not be multiple groups that match this name. " \
                                                    "Response:\n"+str(response)
    if len(response['SecurityGroups']) == 0:
        return None
    else:
        return response['SecurityGroups'][0]


def get_sg_by_id(sg_id):
    client = boto3.client('ec2')
    response = client.describe_security_groups(GroupIds=[sg_id])

    assert not len(response['SecurityGroups']) > 1, "There should not be multiple groups that match this name. " \
                                                    "Response:\n"+str(response)
    if len(response['SecurityGroups']) == 0:
        return None
    else:
        return response['SecurityGroups'][0]



def create_sg():
    client = boto3.client('ec2')
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_security_group
    response = client.create_security_group(
            Description='Security group to enable lustre access',
            GroupName=SECURITY_GROUP_NAME,
            VpcId=VPC_ID,
            # DryRun=True | False
    )
    return response["GroupId"]


def authorize_lustre_inbound(sg_id):
    client = boto3.client('ec2')
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_ingress
    response = client.authorize_security_group_ingress(
            # CidrIp='string',
            # FromPort=123,
            GroupId=sg_id,
            # GroupName='string',
            IpPermissions=[
                {
                    'FromPort': 988,
                    'IpProtocol': 'tcp',
                    'IpRanges': [{'CidrIp':  "0.0.0.0/0",}],
                    'Ipv6Ranges': [{'CidrIpv6': '::/0',}],
                    'ToPort': 988,

                },
            ],
            # IpProtocol='string',
            # SourceSecurityGroupName='string',
            # SourceSecurityGroupOwnerId='string',
            # ToPort=123,
            # DryRun=True | False
    )
    return response


def delete_sg(sg_id):
    client = boto3.client('ec2')
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.delete_security_group
    response = client.delete_security_group(
            GroupId=sg_id,
            # GroupName='string',
            # DryRun=True | False
    )
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("action",
                        choices=["create",
                                 "describe",
                                 "delete",
                                 ])

    args, leftovers = parser.parse_known_args()

    if args.action == "create":
        sg = get_sg()
        if sg is not None:
            raise RuntimeError("Security group already exists. API response:\n"+str(sg))
        sg_id = create_sg()
        authorize_lustre_inbound(sg_id)
        print('Created security group "'+SECURITY_GROUP_NAME+'" ('+sg_id + ')')
    elif args.action == "describe":
        sg = get_sg()
        if sg is None:
            raise RuntimeError("Security group does not exist")
        print(json.dumps(sg, indent=4))
    elif args.action == "delete":
        sg_id = get_sg_id()
        if sg_id is None:
            raise RuntimeError("Security group does not exist")
        response = delete_sg(sg_id)
        print(response)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, "Delete did not return 200:\n"+str(response)
        print("Successfully deleted security group")





