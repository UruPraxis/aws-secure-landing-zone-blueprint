from aws_cdk import Stack, Tags
from constructs import Construct

from urupraxis_secure_landing_zone.network import SecureNetworkConstruct
from urupraxis_secure_landing_zone.endpoints import SecureEndpointsConstruct
from urupraxis_secure_landing_zone.security_audit import SecureAuditConstruct

class LandingZoneStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================
        # COMPONENT 1: SECURITY & COMPLIANCE LAYER
        # =========================================================
        security_layer = SecureAuditConstruct(
            self, "SecurityLayer", 
            environment=environment
        )

        # =========================================================
        # COMPONENT 2: NETWORK LAYER (VPC)
        # =========================================================
        network_layer = SecureNetworkConstruct(
            self, "NetworkLayer", 
            environment=environment
        )

        # =========================================================
        # COMPONENT 3: PRIVATE CONNECTIONS (VPC ENDPOINTS)
        # =========================================================
        endpoints_layer = SecureEndpointsConstruct(
            self, "EndpointsLayer",
            vpc=network_layer.vpc
        )

        # =========================================================
        # RESOURCE TAGGING & RESOURCE EXPOSURE
        # =========================================================
        Tags.of(self).add("Environment", environment)
        Tags.of(self).add("Project", "urupraxis-landing")
