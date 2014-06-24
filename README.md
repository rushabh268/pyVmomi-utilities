pyVmomi-Client-samples
======================

Functions using pyVmomi library to manage VMware virtual machines - includes code dealing with distributed switch.


Functions in the pyVM_funcs.py :

get_obj(content, vimtype, name) - Fetch object from VMware Managed Object Tree based on object name

checktask(task,error_mesg,success_mesg="Success") - Check the status of the task. Need the task object as one of the arguments.

poweronvm(si,content,vmname) - Power on VM.
poweroffvm(si,content,vmname)
resetVM(si,content,vmname)

getVMState(si,content,vmname) - Return the state of the VM.

getmacaddress(si,content,vmname) - Get the mac address of the VM. Assumes a VM with only one VNIC. The mac address can then be passed to other things like foreman.

