from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct

class SecureEndpointsConstruct(Construct):

    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. Crear un Security Group centralizado exclusivo para los VPC Endpoints
        # Principio de Menor Privilegio: Solo permitimos tráfico entrante (puerto 443) 
        # desde adentro de nuestra propia red (VPC CIDR block)
        endpoint_sg = ec2.SecurityGroup(
            self, "VpcEndpointsSG",
            vpc=vpc,
            description="Security Group para el acceso privado a los VPC Endpoints",
            allow_all_outbound=True # Permitir salida para responder las peticiones
        )
        
        endpoint_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="Permitir HTTPS interno desde la VPC hacia los endpoints"
        )

        # 2. Definir los sub-servicios de SSM requeridos para que Session Manager funcione de forma aislada
        # ssm: API general de Systems Manager
        # ssmmessages: Canal de datos bidireccional seguro para la terminal interactiva de Session Manager
        # ec2messages: Requerido por el agente de SSM para comunicarse con el plano de control
        ssm_services = [
            ec2.InterfaceVpcEndpointAwsService.SSM,
            ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES
        ]

        # 3. Desplegar los Interface Endpoints automáticamente en las subredes aisladas de datos
        for index, service in enumerate(ssm_services):
            ec2.InterfaceVpcEndpoint(
                self, f"SSMInterfaceEndpoint-{index}",
                vpc=vpc,
                service=service,
                private_dns_enabled=True, # Clave: Sobrescribe la resolución DNS pública por las IPs locales privadas
                security_groups=[endpoint_sg],
                subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                )
            )

        # 4. Buenas Prácticas de Costos: Agregar el Gateway Endpoint de Amazon S3
        # Los Interface Endpoints cuestan dinero por hora. El Gateway Endpoint de S3 es GRATUITO.
        # El agente de SSM necesita hablar con S3 para descargar actualizaciones y guardar logs de auditoría.
        vpc.add_gateway_endpoint(
            "S3GatewayEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            ]
        )
