from base1 import DeviceAction
import pyswitchlib.asset


class apply_acl(DeviceAction):
    def run(self, mgmt_ip, username, password, intf_type, intf_name,
            rbridge_id, acl_name, acl_direction, acl_type):
        """Run helper methods to apply ACL on desired interface.
        """
        self.setup_connection(host=mgmt_ip, user=username, passwd=password)
        output = {}
        changes = []
        interface_list = []
        intf_type = intf_type.lower()
        try:
            device = self.asset(ip_addr=self.host, auth=self.auth)
            self.logger.info('successfully connected to %s to enable interface', self.host)
        except Exception as e:
            raise ValueError('Failed to connect to %s due to %s', self.host, e.message)

        # Check is the user input for Interface Name is correct
        for intf in intf_name:
            if "-" not in intf:
                interface_list.append(intf)
            else:
                ex_intflist = self.expand_interface_range(intf_type=intf_type, intf_name=intf)
                for ex_intf in ex_intflist:
                    interface_list.append(ex_intf)
        msg = None
        for intf in interface_list:
            if not self.validate_interface(intf_type, intf, rbridge_id):
                msg = "Input is not a valid Interface"
                break
        if msg is None:
            changes = self._apply_acl(device, intf_type=intf_type,
                                      intf_name=interface_list,
                                      rbridge_id=rbridge_id,
                                      acl_name=acl_name,
                                      acl_direction=acl_direction,
                                      acl_type=acl_type
                                      )
        else:
            raise ValueError(msg)
        output['result'] = changes
        self.logger.info('closing connection to %s after applying access-list-- \
                      all done!', self.host)
        return output

    def _apply_acl(self, device, intf_type, intf_name, rbridge_id,
                   acl_name, acl_direction, acl_type):
        result = []
        for intf in intf_name:
            if acl_type == 'routed':
                atype = 'ip'
            elif acl_type == 'switched':
                atype = 'mac'
            elif acl_type == 'routed_ipv6':
                atype = 'ipv6'
            method = 'rbridge_id_interface_{}_{}_access_group_create'. \
                format(intf_type, atype) if rbridge_id \
                else 'interface_{}_{}_access_group_create'.format(intf_type, atype)
            aply_acl = eval('device.{}'.format(method))
            access_grp = (str(acl_name), str(acl_direction), str(acl_type))
            self.logger.info('Applying ACL %s on int-type - %s int-name- %s',
                             acl_name, intf_type, intf)
            try:
                aply = list(aply_acl(rbridge_id, intf, access_grp) \
                                if rbridge_id else list(aply_acl(intf, access_grp)))
                result.append(str(aply[0]))
                if not eval(str(aply[0])):
                    self.logger.info('Cannot apply  %s on interface %s %s due to %s',
                                     acl_name, intf_type, intf,
                                     str(aply[1][0][self.host]['response']['json']['output']))
                else:
                    self.logger.info('Successfully  applied  %s ACL on interface %s %s ',
                                     acl_name, intf_type, intf)
            except Exception as e:
                self.logger.info('Cannot apply  %s on interface %s %s due to %s',
                                 acl_name, intf_type, intf, e.message)
                raise ValueError(e.message)
        return result
