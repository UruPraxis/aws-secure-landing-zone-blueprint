import os
import toml
from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct

class SecureNetworkConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================
        # ENVIRONMENT CONFIGURATION PARSER
        # =========================================================
        config_path = os.path.join(os.getcwd(), "config.toml")
        config = toml.load(config_path)

        vpc_section = f"VPC_{environment}"
        
        vpc_cidr = config[vpc_section]["VPC_CIDR"]
        availability_zones = config[vpc_section]["AVAILABILITY_ZONES"]
        public_mask = config[vpc_section]["PUBLIC_SUBNET_CIDR_MASK"]
        private_mask = config[vpc_section]["PRIVATE_SUBNET_CIDR_MASK"]
        isolated_mask = config[vpc_section]["ISOLATED_SUBNET_CIDR_MASK"]

        resource_prefix = f"urupraxis-{environment}"

        # =========================================================
        # SECURE MULTI-AZ CORE VPC CONFIGURATION
        # =========================================================
        self.vpc = ec2.Vpc(
            self, "Vpc",
            vpc_name=f"{resource_prefix}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            availability_zones=availability_zones,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=public_mask,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=private_mask,
                ),
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=isolated_mask,
                ),
            ],
            # Security Best Practice: Enforce active VPC Flow Logs straight to S3
            flow_logs={
                "FlowLogsToS3": ec2.FlowLogOptions(
                    destination=ec2.FlowLogDestination.to_s3(),
                    traffic_type=ec2.FlowLogTrafficType.ALL
                )
            }
        )
