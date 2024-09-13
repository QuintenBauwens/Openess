import os
import xml.etree.ElementTree as ET
import xmltodict
import Siemens.Engineering as tia
import re
import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")

from System.IO import FileInfo
from core.functionTypes import FUNC_INTERN_CON
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class BlockData():
	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def get_core_classes(self):
		"""
		Returns the project classes.

		Returns:
			list: A list of the project classes.
		"""
		self.software = self.project.software
		self.hardware = self.project.hardware

	def get_core_functions(self):
		logger.debug(f"Accessing 'get_software_container' from the software object '{self.project.software}'...")
		self.software_container = self.software.get_software_container()
		logger.debug(f"Accessing 'get_plc_devices' from the hardware object '{self.project.hardware}'...")
		self.plc_list = self.hardware.get_plc_devices()
	
	def export_block(self, block_name='LSystemVarS7-1500'): # for all the blocks
		logger.debug(f"Exporting block '{block_name}'")
		for plc in self.plc_list:
			block = self.software.find_block(self.software_container[plc.Name].BlockGroup, block_name)

		block_type = block.GetType().Name
		block_number = str(block.Number)
		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}\\Blocks'
		path = os.path.join(cwd + f"\\{block_type}{block_number}.xlm")

		if os.path.exists(path):
			logger.info(f"Block '{path}' already exists, removing and re-exporting...")
			try:
				os.remove(path)
				logger.info(f"Block '{block_type}{block_number}.xml' removed successfully")
			except Exception as e:
				raise ValueError(f"Error in removing block '{block_type}{block_number}.xml': {str(e)}")

		try: # try to export the block
			block.Export(FileInfo(path), tia.ExportOptions.WithDefaults) 
			logger.debug(f"Block '{block_type}{block_number}' exported successfully: '{path}'")
		except: # one of the raison is that the block needs to be compiled
			logger.error(f'Error in exporting blockdata {type}{block.Number}')
			logger.warning('Try to compile Block...')

			result = block.GetService[tia.Compiler.ICompilable]().Compile() # compiling the block
			for message in (result.Messages):
				logger.info((message.Description)) # prit

			try:# if the block is compiled, try to export again
				block.Export(FileInfo(path), tia.ExportOptions.WithDefaults)
				logger.info(f'Re-compiling solved the error')
			except: # for some (safety) blocks the block can not be exported
				raise ValueError('Error not solved by re-compiling')
		return path


	def read_block_xml(self, block_name):
		path = self.export_block(block_name)
		logger.debug(f"Reading xml of '{block_name}'")

		tree = ET.parse(path)
		xml_date = tree.getroot()
		xmlstr = ET.tostring(xml_date, encoding='utf-8', method='xml')
		doc = dict(xmltodict.parse(xmlstr))

		logger.debug(f"Successfully read xml of '{block_name}'")
		return doc


	def search_part(self, network, ns, UId, portname=None):
		if UId is None:
			raise ValueError('UId is not given')
		elif network is None:
			raise ValueError('Please provide a network')
		nwk_source = network['AttributeList']['NetworkSource']
		nwk_part = nwk_source[f'ns{ns}:FlgNet'][f'ns{ns}:Parts'][f'ns{ns}:Part']

		if f'ns{ns}:FlgNet' not in nwk_source.keys():
			raise ValueError(f"'ns{ns}:FlgNet' not found in the network source")
		
		logger.debug(f"Searching for part with UId {UId} in the network, networkID: '{network['@ID']}'")
		for part in nwk_part:
			part_disabled = part['@DisabledENO']
			part_name = part['@Name']
			part_UId = part['@UId']
			
			if (part_UId == UId):
				logger.debug(
					f"Part with UId '{UId}' found in the network: "
					f"part disabled: '{part_disabled}', "
					f"part name: '{part_name}'"
				)
				return part
			else:
				raise ValueError(f"No part with UId {UId} found in the network")


	def search_wire(self, network, ns, compUId=None, partUId=None, portname=None):
		if compUId is None and partUId is None:
			raise ValueError('Provide either a componentUId or a partUId')
		elif network is None:
			raise ValueError('Please provide a network')
		nwk_source = network['AttributeList']['NetworkSource']

		if f'ns{ns}:FlgNet' not in nwk_source.keys():
			raise ValueError(f"'ns{ns}:FlgNet' not found in the network source")

		nwk_wires = nwk_source[f'ns{ns}:FlgNet'][f'ns{ns}:Wires']
		target_ports = []

		try:
			for i, wire in enumerate(nwk_wires[f'ns{ns}:Wire']):
				if f'ns{ns}:IdentCon' not in wire.keys():
					continue
				comp_UId = wire[f'ns{ns}:IdentCon']['@UId'] # get the source of the wire (value)
				part_port = wire[f'ns{ns}:NameCon']['@Name'] # get the target/port where the wite is connected to
				part_UId = wire[f'ns{ns}:NameCon']['@UId'] # get the target/part that the wire goes to
				# the parameter that contains the libVersion should be connected to the input of the move block
				# and the part is the same
				if partUId and portname:
					condition_met = (part_UId == partUId) and (part_port == portname)
					if condition_met:
						return comp_UId
				elif partUId is None:
					condition_met = (comp_UId == compUId)
					if condition_met:
						logger.debug(
							f"Wire-target part found of wire-source '{comp_UId}': "
							f"partUId: '{part_UId}', "
							f"partPort: '{part_port}'"
						)
						return part_UId, part_port
				else:
					raise ValueError('The following is allowed (compUId) or (partUID) or (partUID and portname)')
		except Exception as e:
			raise ValueError(f"Error in searching for the wire: {str(e)}")
		return target_ports


	def search_component(self, network, ns, UId=None, comp_name=None):
		if UId is None and comp_name is None:
			raise ValueError('Provide either a UId or a component name')

		nwk_source = network['AttributeList']['NetworkSource']
		nwk_id = network['@ID']

		if f'ns{ns}:FlgNet' not in nwk_source.keys():
			return
		
		nwk_parts = nwk_source[f'ns{ns}:FlgNet'][f'ns{ns}:Parts']
		nwk_parts_access = nwk_parts[f'ns{ns}:Access']
		
		try:
			for access in nwk_parts_access:
				if (f"ns{ns}:Symbol" in access.keys()):
					component = access[f"ns{ns}:Symbol"][f"ns{ns}:Component"]
				elif (f"ns{ns}:Constant" in access.keys()):
					component = access[f'ns{ns}:Constant']
				else:
					continue
				component_scope = access[f"@Scope"]
				component_UId = access[f"@UId"]
				
				# always make it a list, even if there is only one component
				if not isinstance(component, list):
					component = [component] 

				# check if a network contains the libVersion
				# system lib version gets set by move block
				for j, component in enumerate(component):
					if f'ns{ns}:Part' not in nwk_parts.keys():
						continue

					if UId is None:
						if component_scope != "LiteralConstant":
							if component['@Name'] != comp_name:
								continue
						else:
							continue
					elif comp_name is None:
						if component_UId != UId:
							continue
					else:
						raise ValueError('Provide either a UId or a component name')

					if component_scope == "LiteralConstant":
						logger.debug(
							f"Found component {'with name ' + comp_name if comp_name is not None else 'with UId ' + UId} in network '{self.i_network}': "
							f"networkID: '{nwk_id}', "
							f"componentScope: '{component_scope}', "
							f"componentType: '{component[f'ns{ns}:ConstantType']}', "
							f"componentValue: '{component[f'ns{ns}:ConstantValue']}' "
						)
						return access
					else:
						logger.debug(
							f"Found component {'with name ' + comp_name if comp_name is not None else 'with UId ' + UId}: "
							f"networkID: '{nwk_id}',"
							f"componentScope: '{component_scope}',"
							f"componentName: '{component['@Name']}',"
							f"componentID: '{component_UId}'"
						)
						return access
		except Exception as e:
			raise ValueError(f"Error in searching for the component: {str(e)}")


	def get_para_value(self, network, ns, UId, portname):
		if UId is None:
			raise ValueError('UId is not given')
		elif network is None:
			raise ValueError('Please provide a network')
		try:
			part = self.search_part(network, ns, UId)
			part_name = part['@Name'].lower()

			linked_port = FUNC_INTERN_CON.get(part_name).get(portname)
			if linked_port is None:
				try:
					stripped_portname = re.sub(r'\d+$', '', portname).lower()
					linked_port = FUNC_INTERN_CON.get(part_name).get(stripped_portname)
				except:
					pass
			linked_compUId = self.search_wire(network, ns, partUId=UId, portname=linked_port)

			logger.debug(
				f"Getting linked port of function '{part_name}' and port '{portname}': "
				f"port: '{portname}', "
				f"linked port: '{linked_port}', "
				f"linked component UId: '{linked_compUId}'"
			)
			
			logger.debug(f"Searing component (UId: '{linked_compUId}') to retrieve its value")
			linked_comp = self.search_component(network, ns, UId=linked_compUId)
			linked_compValue = linked_comp[f"ns{ns}:Constant"][f"ns{ns}:ConstantValue"]
			
			return linked_compValue
		except Exception as e:
			raise ValueError(f"Failed to get the value of the parameter: {str(e)}")


	def get_nwk_para(self, block_name, parameter):
		if block_name is None and parameter is None:
			raise ValueError('Provide a block name and a parameter name')
		
		component_name = parameter
		doc = self.read_block_xml(block_name)

		if "SW.Blocks.CompileUnit" not in doc["Document"][f"SW.Blocks.FB"]["ObjectList"].keys():
			raise ValueError("No networks found in block")

		NS = 0
		while True:
			if f'@xmlns:ns{NS}' not in doc['Document'].keys():
				break
			NS += 1

		Network_list = doc['Document']["SW.Blocks.FB"]['ObjectList']['SW.Blocks.CompileUnit']# get the list of all the networks

		logger.debug(
			f"Scanning namespaces in block '{block_name}': "
			f"Total namespaces found: '{NS}', "
			f"Total networks found: '{len(Network_list)}'"
		)
		logger.debug(
			f"Scanning networks of block '{block_name}' for component/parameter with name: '{component_name}'"
		)
		for i, network in enumerate(Network_list):
			self.i_network = i
			for ns in range(NS):
				try:
					component = self.search_component(network, ns, comp_name=component_name)
					if component is None:
						continue
					component_UId = component['@UId']

					logger.debug(f"Searching wire-target of component '{component_name}' with UId: '{component_UId}'")
					wire_target = self.search_wire(network, ns, compUId=component_UId)
					if wire_target is None:
						continue
					part_UId, part_port = wire_target
					
					parameter_value = self.get_para_value(network, ns, part_UId, part_port)
					logger.debug(f"Found value of parameter '{component_name}': '{parameter_value}'")
					return parameter_value
				except ValueError as e:
					raise ValueError(f"Error in namespace '{ns}': {str(e)}")
