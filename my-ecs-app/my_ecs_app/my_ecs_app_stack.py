import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
)
from constructs import Construct

class MyNewCdkAppStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)  # Default is all AZs in the region

        # Create an ECS cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Add capacity to the ECS cluster with increased timeout
        auto_scaling_group = cluster.add_capacity("DefaultAutoScalingGroup",
            instance_type=ec2.InstanceType("t2.micro"),
            desired_capacity=1,
            machine_image=ecs.EcsOptimizedAmi(),
            update_type=ecs.CloudFormationInitUpdateType.REPLACE,
            resource_signal_timeout=cdk.Duration.minutes(10)  # Increased timeout
        )

        # Define a task definition with a single container
        task_definition = ecs.Ec2TaskDefinition(self, "MyTaskDefinition")

        container = task_definition.add_container(
            "MyContainer",
            image=ecs.ContainerImage.from_registry("nginx:latest"),
            memory_limit_mib=512
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=80, host_port=80)
        )

        # Create a service to run the task in the cluster
        service = ecs.Ec2Service(self, "MyService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1
        )

