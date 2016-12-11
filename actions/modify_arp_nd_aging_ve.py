# Copyright 2016 Brocade Communications Systems, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ne_base import NosDeviceAction
import pynos.utilities


class ModifyARPNDAgingVe(NosDeviceAction):
    """
       Implements the logic to create IP ARP or nd aging timeout on a given Ve interface .
       This action acheives the below functionality
       1.Check specified Ve is valid and exists and IP ARP or nd aging timeout is not configured.
       2.Configure IP ARP or ND aging timeout if its not configured on Ve.
    """

    def run(self, mgmt_ip, username, password, vlan_id, arp_aging_type, arp_aging_timeout,
            nd_cache_expire_time, rbridge_id):
        """Run helper methods to implement the desired state.
        """
        self.setup_connection(host=mgmt_ip, user=username, passwd=password)
        changes = {}

        with self.mgr(conn=self.conn, auth=self.auth) as device:
            self.logger.info('successfully connected to %s to create IP ARP/ND aging timeout on Ve',
                             self.host)
            if rbridge_id is None:
                rb_list = self._vlag_pair(device)
            else:
                rb_list = rbridge_id
            for rbridge_id in rb_list:
                vlan_arp_nd_check_pass = self._check_requirements_arp_nd_check(device,
                                                                               vlan_id,
                                                                               arp_aging_type,
                                                                               rbridge_id)
                if vlan_arp_nd_check_pass:
                    if arp_aging_type == 'arp_aging':
                        changes['create_arp_nd_check'] = self._create_arp_nd(device, vlan_id,
                                                                             arp_aging_timeout,
                                                                             rbridge_id)
                    else:
                        changes['create_arp_nd_check'] = "Not supported"
                        self.logger.info('configuring ND cache expire time isnot allowed currently')
            self.logger.info(
                'closing connection to %s after configuring'
                'IP ARP/ND aging timeout on Ve -- all done!', self.host)
        return changes

    def _check_requirements_arp_nd_check(self, device, vlan_id, arp_aging_type, rbridge_id):
        """Fail the task if Ve exists and IP ARP/ND aging timeout exists .
        """
        valid_ve = self._validate_if_ve_exists(device, vlan_id)
        if not valid_ve:
            self.logger.info("Ve interface not configured on rbridge %s", rbridge_id)
            return False
        get_code = device.interface.int_ipv4_arp_aging_timout(get=True, int_type='ve',
                                                              name=vlan_id,
                                                              rbridge_id=rbridge_id)
        if get_code.data.find('.//{*}arp-aging-timeout') is not None:
            get_code = get_code.data.find('.//{*}arp-aging-timeout').text
            if str(get_code) == '240':
                return True
            else:
                self.logger.info("IP ARP aging timeout already configured"
                                 "on rbridge %s", rbridge_id)
                return False
        return True

    def _create_arp_nd(self, device, vlan_id, arp_aging_timeout, rbridge_id):
        """ Configuring IP ARP aging timeout on Ve interface."""
        try:
            device.interface.int_ipv4_arp_aging_timout(int_type='ve', name=vlan_id,
                                                       arp_aging_timeout=str(arp_aging_timeout),
                                                       rbridge_id=rbridge_id)
            self.logger.info("IP ARP aging timeout configured on rbridge %s", rbridge_id)
        except ValueError:
            self.logger.info("Configuring IP ARP aging timeout failed")
            return False
        return True

    def _validate_if_ve_exists(self, device, vlan_id):
        """validate vlan_id exists.
        """

        valid_vlan = pynos.utilities.valid_vlan_id(vlan_id=vlan_id, extended=True)
        if not valid_vlan:
            self.logger.info('Invalid VLAN id %s', vlan_id)
            return False

        vlan_list = device.interface.ve_interfaces()
        for each_ve in vlan_list:
            if 'Ve' in each_ve['if-name'] and vlan_id in each_ve['if-name']:
                return True
        return False

    def _vlag_pair(self, device):
        """ Fetch the RB list if VLAG is configured"""

        rb_list = []
        result = device.vcs.vcs_nodes
        for each_rb in result:
            rb_list.append(each_rb['node-rbridge-id'])
        if len(rb_list) >= 3:
            raise ValueError('VLAG PAIR must be <= 2 leaf nodes')
        return list(set(rb_list))
