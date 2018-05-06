from aws_create_vm_mod import init_session, init_ec2client
import aws_inventory as i


def main():
    print("getting into aws...")
    ec2 = init_session()
    ec2client = init_ec2client()
    print("terminating instance...")
    inst = ec2.Instance(id=i.instance_id)
    inst.terminate()
    inst.wait_until_terminated()
    print("deleting key pair...")
    ec2client.delete_key_pair(KeyName='vtestkeypair')
    print("deleting subnet...")
    ec2client.delete_subnet(SubnetId=i.subnet_id)
    print("detaching ig from vpc..")
    vpc = ec2.Vpc(id=i.vpc_id)
    vpc.detach_internet_gateway(InternetGatewayId=i.ig_id)
    print("deleting ig...")
    ec2client.delete_internet_gateway(InternetGatewayId=i.ig_id)
    print("deleting vpc...")
    ec2client.delete_vpc(VpcId=i.vpc_id)


if __name__ == '__main__':
    main()





