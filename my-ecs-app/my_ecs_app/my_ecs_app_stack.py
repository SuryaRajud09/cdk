import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_ecr as ecr,
    aws_iam as iam,
)
from constructs import Construct

class MyNewCdkAppStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC with 2 availability zones and public/private subnets
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # Create a Security Group for the ECS instances
        security_group = ec2.SecurityGroup(self, "ECSSecurityGroup",
            vpc=vpc,
            description="Allow HTTP traffic",
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic from anywhere"
        )

        # Create an ECS cluster in the VPC
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Create an Auto Scaling Group for EC2 instances in public subnets with public IP assignment
        auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.medium"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux(),
            desired_capacity=2,
            associate_public_ip_address=True,  # Auto-assign public IP addresses
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=security_group  # Attach the security group
        )

        # Attach a role with ECS permissions to the instances
        auto_scaling_group.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role")
        )

        # Create a capacity provider for the ECS cluster using the Auto Scaling Group
        capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group
        )

        # Attach the capacity provider to the ECS cluster
        cluster.add_asg_capacity_provider(capacity_provider)

        # Reference the ECR repository by its name and tag
        repository = ecr.Repository.from_repository_name(self, "MyECRRepo",
            repository_name="cdk-hnb659fds-container-assets-146580983502-us-east-1"
        )

        # Create the IAM role for ECS task execution
        execution_role = iam.Role(self, "EcsTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        execution_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"))

        # Define a task definition with a container using the ECR image
        task_definition = ecs.Ec2TaskDefinition(self, "MyTaskDefinition",
            execution_role=execution_role  # Attach the execution role to the task definition
        )

        container = task_definition.add_container("MyContainer",
            image=ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            memory_limit_mib=512
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=80, host_port=80)
        )

        # Create an ECS service to run the task definition in the cluster
        service = ecs.Ec2Service(self, "MyService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2
        )
