import boto3
import base64

def init_session():
    ec2 = boto3.resource("ec2")
    return ec2


def init_ec2client():
    ec2client = boto3.client('ec2')
    return ec2client


def create_keypair(ec2):
    keypair = ec2.create_key_pair(KeyName='vtestkeypair')
    with open("vtestkeypair.pem", "w+") as f:
        f.write(keypair.key_material)


def create_vpc(ec2):
    """vpc"""
    vpc = ec2.create_vpc(CidrBlock='10.222.0.0/16')
    vpc.create_tags(Tags=[{"Key": "Name", "Value": "vtest-vpc"}])
    vpc.wait_until_available()
    print(vpc.id)
    return vpc


def create_subnet(ec2, vpc):
    """subnet"""
    subnet = ec2.create_subnet(CidrBlock='10.222.22.0/24', VpcId=vpc.id)
    subnet.create_tags(Tags=[{"Key": "Name", "Value": "vtest-subnet"}])
    print(subnet.id)
    return subnet


def create_ig(ec2, vpc):
    """internet gateway"""
    ig = ec2.create_internet_gateway()
    ig.create_tags(Tags=[{"Key": "Name", "Value": "vtest-ig"}])
    vpc.attach_internet_gateway(InternetGatewayId=ig.id)
    print(ig.id)
    return ig


def create_rt(ec2, vpc, subnet, ig):
    rt = ec2.RouteTable(list(vpc.route_tables.all())[0].id)
    rt.associate_with_subnet(SubnetId=subnet.id)
    rt.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=ig.id,
    )


def create_sg(ec2, vpc):
    sg = ec2.SecurityGroup(list(vpc.security_groups.all())[0].id)
    sg.create_tags(Tags=[{"Key": "Name", "Value": "vtest-sg"}])
    sg.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='icmp',
        FromPort=-1,
        ToPort=-1
    )
    sg.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='tcp',
        FromPort=22,
        ToPort=22
    )
    sg.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='udp',
        FromPort=1194,
        ToPort=1194
    )
    print(sg.id)
    return sg

def dump_provision_file():
    with open('aws_provision.sh', 'r') as f:
        dump = f.read()
        dump64 = base64.b64encode(bytes(dump, 'utf-8'))
    return dump64



def create_instance(ec2, subnet, sg, provision):
    instances = ec2.create_instances(ImageId='ami-0189d76e',
                                     InstanceType='t2.micro',
                                     MaxCount=1, MinCount=1,
                                     KeyName='vtestkeypair',
                                     UserData=provision,
                                     NetworkInterfaces=[{'SubnetId': subnet.id,
                                                         'DeviceIndex': 0,
                                                         'AssociatePublicIpAddress': True,
                                                         'Groups': [sg.group_id]}])
    instances[0].wait_until_running()
    instance = ec2.Instance(id=instances[0].id)
    instance.create_tags(Tags=[{"Key": "Name", "Value": "vtest-instance"}])
    return instance

def print_ssh_command():
    pass

if __name__ == '__main__':
    print("creating session..."+"\n")
    ec2 = init_session()
    ec2client = init_ec2client()

    print("creating vpc...")
    vpc = create_vpc(ec2)
    print("[OK] " + vpc.id + "\n")

    print("creating subnet...")
    subnet = create_subnet(ec2,vpc)
    print("[OK] " + subnet.id+"\n")

    print("creating internet gateway...")
    ig = create_ig(ec2, vpc)
    print("[OK] " + ig.id+"\n")

    print("configure routing table..."+"\n")
    create_rt(ec2, vpc, subnet, ig)

    print("creating security group...")
    sg = create_sg(ec2, vpc)
    print("[OK] " + sg.id+"\n")

    print("creating key pair..."+"\n")
    create_keypair(ec2)

    provision = dump_provision_file()

    print("creating instance...")
    instance = create_instance(ec2, subnet, sg, provision)
    print("[OK] "+instance.id+"\n")
    with open('aws_inventory.py', 'w+') as f:
        f.write('instance_id ='+'"'+instance.id+'"'+ "\n")
        f.write("subnet_id ="+'"'+subnet.id+'"' + "\n")
        f.write("ig_id ="+'"'+ig.id+'"'+"\n")
        f.write("vpc_id ="+'"'+vpc.id+'"')
    public_ip = ec2client.describe_instances(Filters=[{'Name':'instance-id','Values':[instance.id]}])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
    print ("use this command to get to the server:\nssh -i vtestkeypair.pem ubuntu@"+public_ip)
