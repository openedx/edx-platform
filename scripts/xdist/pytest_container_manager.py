import argparse
import logging
import time

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PytestContainerManager():
    """
    Responsible for spinning up and terminating containers to be used with pytest-xdist
    """

    def __init__(self, region, cluster):
        self.ecs = boto3.client('ecs', region)
        self.cluster_name = cluster

    def spin_up_containers(self, number_of_containers, task_name, subnets, security_groups, public_ip, launch_type):
        """
        Spins up containers and generates two .txt files, one containing the IP
        addresses of the new containers, the other containing their task_arns.
        """
        CONTAINER_RUN_TIME_OUT_MINUTES = 10
        MAX_RUN_TASK_RETRIES = 7

        revision = self.ecs.describe_task_definition(taskDefinition=task_name)['taskDefinition']['revision']
        task_definition = "{}:{}".format(task_name, revision)

        logging.info("Spinning up {} containers based on task definition: {}".format(number_of_containers, task_definition))

        remainder = number_of_containers % 10
        quotient = number_of_containers / 10

        container_num_list = [10 for i in range(0, quotient)]
        if remainder:
            container_num_list.append(remainder)

        # Boot up containers. boto3's run_task only allows 10 containers to be launched at a time
        task_arns = []
        for num in container_num_list:
            for retry in range(1, MAX_RUN_TASK_RETRIES + 1):
                try:
                    response = self.ecs.run_task(
                        count=num,
                        cluster=self.cluster_name,
                        launchType=launch_type,
                        networkConfiguration={
                            'awsvpcConfiguration': {
                                'subnets': subnets,
                                'securityGroups': security_groups,
                                'assignPublicIp': public_ip
                            }
                        },
                        taskDefinition=task_definition
                    )
                except ClientError as err:
                    # Handle AWS throttling with an exponential backoff
                    if retry == MAX_RUN_TASK_RETRIES:
                        raise StandardError(
                            "MAX_RUN_TASK_RETRIES ({}) reached while spinning up containers due to AWS throttling.".format(MAX_RUN_TASK_RETRIES)
                        )
                    logger.info("Hit error: {}. Retrying".format(err))
                    countdown = 2 ** retry
                    logger.info("Sleeping for {} seconds".format(countdown))
                    time.sleep(countdown)
                else:
                    break

            for task_response in response['tasks']:
                task_arns.append(task_response['taskArn'])

        # Wait for containers to finish spinning up
        not_running = task_arns[:]
        ip_addresses = []
        all_running = False
        for attempt in range(0, CONTAINER_RUN_TIME_OUT_MINUTES * 2):
            time.sleep(30)
            list_tasks_response = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=not_running)['tasks']
            del not_running[:]
            for task_response in list_tasks_response:
                if task_response['lastStatus'] == 'RUNNING':
                    for container in task_response['containers']:
                        ip_addresses.append(container["networkInterfaces"][0]["privateIpv4Address"])
                else:
                    not_running.append(task_response['taskArn'])

            if not_running:
                logger.info("Still waiting on {} containers to spin up".format(len(not_running)))
            else:
                logger.info("Finished spinning up containers")
                all_running = True
                break

        if not all_running:
            raise StandardError(
                "Timed out waiting to spin up all containers."
            )

        logger.info("Successfully booted up {} containers.".format(number_of_containers))

        # Generate .txt files containing IP addresses and task arns
        ip_list_string = " ".join(ip_addresses)
        logger.info("Container IP list: {}".format(ip_list_string))
        ip_list_file = open("pytest_container_ip_list.txt", "w")
        ip_list_file.write(ip_list_string)
        ip_list_file.close()

        task_arn_list_string = " ".join(task_arns)
        logger.info("Container task arn list: {}".format(task_arn_list_string))
        task_arn_file = open("pytest_container_task_arns.txt", "w")
        task_arn_file.write(task_arn_list_string)
        task_arn_file.close()

    def terminate_containers(self, task_arns, reason):
        """
        Terminates containers based on a list of task_arns.
        """
        for task_arn in task_arns:
            response = self.ecs.stop_task(
                cluster=self.cluster_name,
                task=task_arn,
                reason=reason
            )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="PytestContainerManager, manages ECS containers in an AWS cluster."
    )

    parser.add_argument('--region', '-g', default='us-east-1',
                        help="AWS region where ECS infrastructure lives. Defaults to us-east-1")

    parser.add_argument('--cluster', '-c', default="jenkins-worker-containers",
                        help="AWS Cluster name where the containers live. Defaults to"
                        "the testeng cluster: jenkins-worker-containers")

    parser.add_argument('--action', '-a', choices=['up', 'down'], default=None,
                        help="Action for PytestContainerManager to perform. "
                        "Either up for spinning up  AWS ECS containers or down for stopping them")

    # Spinning up containers
    parser.add_argument('--num_containers', '-n', type=int, default=None,
                        help="Number of containers to spin up")

    parser.add_argument('--task_name', '-t', default=None,
                        help="Name of the task definition for spinning up workers")

    parser.add_argument('--subnets', '-s', nargs='+', default=None,
                        help="List of subnets for the containers to exist in")

    parser.add_argument('--security_groups', '-sg', nargs='+', default=None,
                        help="List of security groups to apply to the containers")

    parser.add_argument('--public_ip', choices=['ENABLED', 'DISABLED'],
                        default='DISABLED', help="Whether the containers should have a public IP")

    parser.add_argument('--launch_type', default='FARGATE', choices=['EC2', 'FARGATE'],
                        help="ECS launch type of container. Defaults to FARGATE")

    # Terminating containers
    parser.add_argument('--task_arns', '-arns', nargs='+', default=None,
                        help="Task arns to terminate")

    parser.add_argument('--reason', '-r', default="Finished executing tests",
                        help="Reason for terminating containers")

    args = parser.parse_args()
    containerManager = PytestContainerManager(args.region, args.cluster)

    if args.action == 'up':
        containerManager.spin_up_containers(
            args.num_containers,
            args.task_name,
            args.subnets,
            args.security_groups,
            args.public_ip,
            args.launch_type
        )
    elif args.action == 'down':
        containerManager.terminate_containers(
            args.task_arns,
            args.reason
        )
    else:
        logger.info("No action specified for PytestContainerManager")
