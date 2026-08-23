import os
import toml
from aws_cdk import (
    aws_kms as kms,
    aws_s3 as s3,
    aws_cloudtrail as cloudtrail,
    aws_guardduty as guardduty,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class SecureAuditConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================
        # ENVIRONMENT CONFIGURATION PARSER
        # =========================================================
        config_path = os.path.join(os.getcwd(), "config.toml")
        config = toml.load(config_path)

        sec_section = f"SECURITY_{environment}"
        
        strict_sec = config[sec_section]["ENABLE_STRICT_SECURITY"]
        versioned = config[sec_section]["VERSIONED"]
        destroy_policy = config[sec_section]["REMOVAL_POLICY_DESTROY"]
        expiration_days = config[sec_section]["EXPIRATION_DAYS"]

        rem_policy = RemovalPolicy.DESTROY if destroy_policy else RemovalPolicy.RETAIN

        # =========================================================
        # KMS CUSTOMER MANAGED KEY (CMK)
        # =========================================================
        self.kms_key = kms.Key(
            self, "CoreKey",
            alias=f"alias/urupraxis-core-key-{environment}",
            enable_key_rotation=True, # Required for ISO 27001 / PCI-DSS compliance
            removal_policy=rem_policy
        )

        # =========================================================
        # HARDENED S3 AUDIT LOG STORAGE
        # =========================================================
        audit_bucket = s3.Bucket(
            self, "AuditBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL, # Strict perimeter block
            enforce_ssl=True, # Enforce secure TLS 1.2+ encrypted transport
            versioned=versioned, # Anti-ransomware object protection
            removal_policy=rem_policy,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToGlacier",
                    enabled=strict_sec,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(expiration_days) # Dynamic archival retention
                        )
                    ]
                )
            ]
        )

        # =========================================================
        # AWS CLOUDTRAIL GOVERNANCE ENGINE
        # =========================================================
        self.trail = cloudtrail.Trail(
            self, "ManagementTrail",
            bucket=audit_bucket,
            encryption_key=self.kms_key,
            management_events=cloudtrail.ReadWriteType.ALL,
            include_global_service_events=True # Tracks global IAM mutations regional-wide
        )

        # =========================================================
        # AMAZON GUARDDUTY INTELLIGENT THREAT DETECTION
        # =========================================================
        self.guardduty_detector = guardduty.CfnDetector(
            self, "ThreatDetector",
            enable=True
        )
