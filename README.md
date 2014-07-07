pyVmomi-Client-samples
======================

Utility functions using pyVmomi library to manage VMware virtual machines - includes code dealing with distributed switch. 


Functions in the pyVM_utils.py :

connect_vc() - Connects to the virtual center and returns a Service Instance object.

get_obj(content, vimtype, name) - Fetch object from VMware Managed Object Tree based on object name

checktask(task,error_mesg,success_mesg="Success") - Check the status of the task. Need the task object as one of the arguments.

poweronvm(si,content,vmname) - Power on VM.
poweroffvm(si,content,vmname)
resetVM(si,content,vmname)

getVMState(si,content,vmname) - Return the state of the VM.

getmacaddress(si,content,vmname) - Get the mac address of the VM. Assumes a VM with only one VNIC. The mac address can then be passed to other things like foreman.

changeEth0Network(si,content,vmname,targetnet) - Change the port group to which the VNIC is connected.

create_vm(si,content,clustername,datastorename,buildnetwork,vmname) - Create (not Clone) a VM with one ethernet interface and a single virtual disk on the target cluster and datastore.  Once the VM is created you need to use your own OS provisioning methods to install the OS. buildnetwork is the portgroup to which the VM will be connected.

