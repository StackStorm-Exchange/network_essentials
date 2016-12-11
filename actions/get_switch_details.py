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


class GetSwitchDetails(NosDeviceAction):
    """
       Implements the logic to get switch details from VCS Fabric
       This action acheives the below functionality
    """

    def run(self, mgmt_ip, username, password):
        """Run helper methods to implement the desired state.
        """
        self.setup_connection(host=mgmt_ip, user=username, passwd=password)

        changes = {}
        try:
            with self.mgr(conn=self.conn, auth=self.auth) as device:
                self.logger.info('successfully connected to %s to get switch details', self.host)
                changes['switch_details'] = self._get_switch_details(device, mgmt_ip)
                self.logger.info('closing connection to %s after getting switch details - \
                                 all done!', self.host)
        except Exception, e:
            raise ValueError(e)

        return changes

    def _get_switch_details(self, device, host):
        """get the switch details.
        """
        sw_info = {}
        vcs_info = device.vcs.vcs_nodes
        rb_list = []

        for vcs in vcs_info:
            rb_list.append(vcs['node-rbridge-id'])
            if vcs['node-is-principal'] == "true" and vcs['node-switch-ip'] == host:
                sw_info['switch_ip'] = vcs['node-switch-ip']
                sw_info['principal_ip'] = vcs['node-switch-ip']
                break

            if vcs['node-is-principal'] == "true" and vcs['node-switch-ip'] != host:
                sw_info['principal_ip'] = vcs['node-switch-ip']

            if vcs['node-is-principal'] == "false" and vcs['node-switch-ip'] == host:
                sw_info['switch_ip'] = vcs['node-switch-ip']

        sw_info['rbridge_id'] = rb_list

        return sw_info
