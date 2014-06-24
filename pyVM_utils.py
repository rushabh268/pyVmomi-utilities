#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

'''
References:
http://www.slideshare.net/heyitspablo/vmware-vsphere-api-best-practices
'''


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    print "get_obj: %s"%obj.name
    return obj


def checktask(task,error_mesg,success_mesg="Success"):
	while task.info.state == vim.TaskInfo.State.running:
       		time.sleep(2)

	if task.info.state != vim.TaskInfo.State.success:
		print "%s: %s"%(error_mesg,task.info.error)
		return (task.info.error,False)
	else:
		print "%s"%(success_mesg)
		return (task.info.result,True)


def poweronvm(si,content,vmname):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)
	print "Powering on vm %s ..."%newvm
	err_mesg = "Error in powring on vm %s"%newvm
	success_mesg = "Successfully  powered on vm %s"%newvm
	task = newvm.PowerOnVM_Task()
	(status_mesg,status) = checktask(task,err_mesg,success_mesg)
	return (status_mesg,status)

def poweroffvm(si,content,vmname):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)
	print "Powering off vm %s ..."%newvm
	err_mesg = "Error in powring off vm %s"%newvm
	success_mesg = "Successfully  powered off vm %s"%newvm
	task = newvm.PowerOffVM_Task()
	(status_mesg,status) = checktask(task,err_mesg,success_mesg)
	return (status_mesg,status)
	

def resetVM(si,content,vmname):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)
	print "Resetting vm %s ..."%newvm
	err_mesg = "Error in resetting vm %s"%newvm
	success_mesg = "Successfully reset vm %s"%newvm
	task = newvm.ResetVM_Task()
	(status_mesg,status) = checktask(task,err_mesg,success_mesg)
	return (status_mesg,status)

def getVMState(si,content,vmname):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)	
	return newvm.runtime.powerState
	
def getmacaddress(si,content,vmname):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)	
	vmdev = newvm.config.hardware.device
	
	for dev in vmdev:
		if type(dev) is vim.vm.device.VirtualE1000:
			return dev.macAddress
			break	

def changeEth0Network(si,content,vmname,targetnet):
	newvm = content.searchIndex.FindChild(content.rootFolder.childEntity[0].vmFolder,vmname)	
	vmdev = newvm.config.hardware.device

 	vnic1 = vim.vm.device.VirtualDeviceSpec()
        vnic1.operation = "edit"
	for dev in vmdev:
               if type(dev) is vim.vm.device.VirtualE1000:
			vnic1.device = dev

        '''
        Oh!! DVSwitch ..... grrrr
        #https://github.com/vmware/pyvmomi/issues/33
        '''
        pg_obj = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], targetnet)
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey= pg_obj.key
        dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
        vnic1.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        vnic1.device.backing.port = dvs_port_connection
        vnic1.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        vnic1.device.connectable.startConnected = True

        vdevicelist = []
        vdevicelist.append(vnic1)

        cspec = vim.vm.ConfigSpec()
        cspec.deviceChange = vdevicelist	

	task = newvm.ReconfigVM_Task(cspec)
	(status_mesg,task_status) = checktask(task,"Error in creating vm:")
	return (status_mesg,task_status)

def connect_vc(hostname,username,password):
	si = None
	si = SmartConnect(host=hostname,user=username, pwd=password, port=443)
	content = si.RetrieveContent()
	return (si,content)

def create_vm(si,content,clustername,datastorename,buildnetwork,vmname):

	'''
	First get the resourcepool attached to the target cluster.
	Then create the vm using the vmFolder object at the datacenter level.
	'''


	clusterList = si.content.rootFolder.childEntity[0].hostFolder.childEntity
	dc = si.content.rootFolder.childEntity[0]

	print "Datacenter: %s"%dc.name

	'''
	Looks like FileInfo is really manadatory
	'''

	fspec = vim.vm.FileInfo()
	fspec.vmPathName = "[%s]%s/%s.vmx"%(datastorename,vmname,vmname)


	'''
	Initialize Disk and NIC vmdevice
	'''
	vdisk1 = vim.vm.device.VirtualDisk(capacityInKB = 64000000)
	vdisk1.unitNumber = 0
	vdisk1.controllerKey = 1
	vdisk1BackingInfo = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
	vdisk1BackingInfo.diskMode = "persistent"
	vdisk1.backing = vdisk1BackingInfo
	vdiskspec = vim.vm.device.VirtualDeviceSpec()
	vdiskspec.device = vdisk1
	vdiskspec.fileOperation = "create"
	vdiskspec.operation = "add"

	vctl1 = vim.vm.device.ParaVirtualSCSIController()
	vctl1.key = 1
	vctl1.sharedBus = "noSharing"
	vctlspec = vim.vm.device.VirtualDeviceSpec()
	vctlspec.device = vctl1
	vctlspec.operation = "add"


	vnic1 = vim.vm.device.VirtualDeviceSpec()
	vnic1.operation = "add"
	vnic1.device = vim.vm.device.VirtualE1000()
	vnic1.device.key = 1

	'''
	Oh!! DVSwitch ..... grrrr
	#https://github.com/vmware/pyvmomi/issues/33
	'''
	pg_obj = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], buildnetwork)
	dvs_port_connection = vim.dvs.PortConnection()
	dvs_port_connection.portgroupKey= pg_obj.key
	dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
	vnic1.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
	vnic1.device.backing.port = dvs_port_connection
	vnic1.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
	vnic1.device.connectable.startConnected = True



	vdevicelist = []
	vdevicelist.append(vctlspec)
	vdevicelist.append(vdiskspec)
	vdevicelist.append(vnic1)



	cspec = vim.vm.ConfigSpec()
	cspec.name = vmname 
	cspec.annotation = "Test vsphere API"
	cspec.files = fspec
	cspec.guestId = "centos64Guest"
	cspec.memoryMB = 2048
	cspec.deviceChange = vdevicelist





	for cluster in clusterList:
		if cluster.name == clustername:
			rp = cluster.resourcePool
			print ("Creating vm %s in %s"%(vmname,cluster.name))
			print type(cspec)
			#task = rp.CreateChildVM_Task(config=cspec)
			task = dc.vmFolder.CreateVM_Task(config=cspec,pool=rp)
			(status_mesg,task_status) = checktask(task,"Error in creating vm:")
			return (status_mesg,task_status)


'''
Main
Change the config parameters as per your environment
'''

if __name__ == "__main__":
	config = {}
	config['buildnetwork'] = "PortGroupName"
	config['clustername'] = "ClusterName"
	config['datastorename'] = "DataStoreName"
	config['vmname'] = "vmname"
	config['vcname'] = "virtualcenter_name_or_ip"
	config['username'] = "virtualcenter_login"
	config['password'] = "virtualcenter_password"

	si,content = connect_vc(config['vcname'],config['username'],config['password'])
	'''
	if (create_vm(si,content,config['clustername'],config['datastorename'],config['buildnetwork'],config['vmname'])):
			print getmacaddress(si,content,config['vmname'])
			poweronvm(si,content,config['vmname'])
	'''
	print (getVMState(si,content,"vmname"))
