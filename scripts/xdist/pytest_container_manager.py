import argparse
import logging
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PytestContainerManager():
    """
    Responsible for spinning up and terminating ECS tasks to be used with pytest-xdist
    """
    TASK_RUN_TIMEOUT_MINUTES = 10
    MAX_RUN_TASK_RETRIES = 7

    def __init__(self, region, cluster):
        config = Config(
            retries={
                'max_attempts': self.MAX_RUN_TASK_RETRIES
            }
        )
        self.ecs = boto3.client('ecs', region, config=config)
        self.cluster_name = cluster

    def spin_up_tasks(self, number_of_tasks, task_name, subnets, security_groups, public_ip, launch_type):
        """
        Spins up tasks and generates two .txt files, containing the IP/ arns
        of the new tasks.
        """
        revision = self.ecs.describe_task_definition(taskDefinition=task_name)['taskDefinition']['revision']
        task_definition = "{}:{}".format(task_name, revision)

        logging.info("Spinning up {} tasks based on task definition: {}".format(number_of_tasks, task_definition))

        remainder = number_of_tasks % 10
        quotient = number_of_tasks / 10

        task_num_list = [10 for i in range(0, quotient)]
        if remainder:
            task_num_list.append(remainder)

        # Spin up tasks. boto3's run_task only allows 10 tasks to be launched at a time
        task_arns = []
        for num in task_num_list:
            for retry in range(1, self.MAX_RUN_TASK_RETRIES + 1):
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
                    if retry == self.MAX_RUN_TASK_RETRIES:
                        raise StandardError(
                            "MAX_RUN_TASK_RETRIES ({}) reached while spinning up tasks due to AWS throttling.".format(self.MAX_RUN_TASK_RETRIES)
                        )
                    logger.info("Hit error: {}. Retrying".format(err))
                    countdown = 2 ** retry
                    logger.info("Sleeping for {} seconds".format(countdown))
                    time.sleep(countdown)
                else:
                    break

            for task_response in response['tasks']:
                task_arns.append(task_response['taskArn'])

            failure_array = response['failures']
            if failure_array:
                raise StandardError(
                    "There was at least one failure when spinning up tasks: {}".format(failure_array)
                )

        # Wait for tasks to finish spinning up
        not_running = task_arns[:]
        ip_addresses = []
        all_running = False
        for attempt in range(0, self.TASK_RUN_TIMEOUT_MINUTES * 2):
            time.sleep(30)
            list_tasks_response = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=not_running)['tasks']
            del not_running[:]
            for task_response in list_tasks_response:
                if task_response['lastStatus'] == 'RUNNING':
                    for container in task_response['containers']:
                        container_ip_address = container["networkInterfaces"][0]["privateIpv4Address"]
                        if container_ip_address not in ip_addresses:
                            ip_addresses.append(container_ip_address)
                else:
                    not_running.append(task_response['taskArn'])

            if not_running:
                logger.info("Still waiting on {} tasks to spin up".format(len(not_running)))
            else:
                logger.info("Finished spinning up tasks")
                all_running = True
                break

        if not all_running:
            raise StandardError(
                "Timed out waiting to spin up all tasks."
            )

        logger.info("Successfully booted up {} tasks.".format(number_of_tasks))

        # Generate .txt files containing IP addresses and task arns
        ip_list_string = ",".join(ip_addresses)
        logger.info("Task IP list: {}".format(ip_list_string))
        ip_list_file = open("pytest_task_ips.txt", "w")
        ip_list_file.write(ip_list_string)
        ip_list_file.close()

        task_arn_list_string = ",".join(task_arns)
        logger.info("Task arn list: {}".format(task_arn_list_string))
        task_arn_file = open("pytest_task_arns.txt", "w")
        task_arn_file.write(task_arn_list_string)
        task_arn_file.close()

    def terminate_tasks(self, task_arns, reason):
        """
        Terminates tasks based on a list of task_arns.
        """
        for task_arn in task_arns.split(','):
            response = self.ecs.stop_task(
                cluster=self.cluster_name,
                task=task_arn,
                reason=reason
            )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="PytestContainerManager, manages ECS tasks in an AWS cluster."
    )

    parser.add_argument('--action', '-a', choices=['up', 'down'], default=None,
                        help="Action for PytestContainerManager to perform. "
                        "Either up for spinning up AWS ECS tasks or down for stopping them")

    parser.add_argument('--cluster', '-c', default="jenkins-worker-containers",
                        help="AWS Cluster name where the tasks run. Defaults to"
                        "the testeng cluster: jenkins-worker-containers")

    parser.add_argument('--region', '-g', default='us-east-1',
                        help="AWS region where ECS infrastructure lives. Defaults to us-east-1")

    # Spinning up tasks
    parser.add_argument('--launch_type', default='FARGATE', choices=['EC2', 'FARGATE'],
                        help="ECS launch type for tasks. Defaults to FARGATE")

    parser.add_argument('--num_tasks', '-n', type=int, default=None,
                        help="Number of ECS tasks to spin up")

    parser.add_argument('--public_ip', choices=['ENABLED', 'DISABLED'],
                        default='DISABLED', help="Whether the tasks should have a public IP")

    parser.add_argument('--subnets', '-s', nargs='+', default=None,
                        help="List of subnets for the tasks to exist in")

    parser.add_argument('--security_groups', '-sg', nargs='+', default=None,
                        help="List of security groups to apply to the tasks")

    parser.add_argument('--task_name', '-t', default=None,
                        help="Name of the task definition")

    # Terminating tasks
    parser.add_argument('--reason', '-r', default="Finished executing tests",
                        help="Reason for terminating tasks")

    parser.add_argument('--task_arns', '-arns', default=None,
                        help="Task arns to terminate")

    args = parser.parse_args()
    containerManager = PytestContainerManager(args.region, args.cluster)

    if args.action == 'up':
        containerManager.spin_up_tasks(
            args.num_tasks,
            args.task_name,
            args.subnets,
            args.security_groups,
            args.public_ip,
            args.launch_type
        )
    elif args.action == 'down':
        containerManager.terminate_tasks(
            args.task_arns,
            args.reason
        )
    else:
        logger.info("No action specified for PytestContainerManager")
