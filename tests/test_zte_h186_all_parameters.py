# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

import unittest
import xml.etree.ElementTree as ET

from zte_h186_stats import extract_xml, xml_values, normalize_to_ha

SAMPLE_ROUTER_XML = """
<ajax_response_xml_root>
    <IF_ERRORSTR>SUCC</IF_ERRORSTR>
    <Instance>
        <ParaName>Status</ParaName>
        <ParaValue>Up</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Module_type</ParaName>
        <ParaValue>VDSL2</ParaValue>
    </Instance>
    <Instance>
        <ParaName>CurrentProfile</ParaName>
        <ParaValue>17a</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_current_rate</ParaName>
        <ParaValue>109200</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_current_rate</ParaName>
        <ParaValue>42800</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_max_rate</ParaName>
        <ParaValue>118500</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_max_rate</ParaName>
        <ParaValue>46100</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_noise_margin</ParaName>
        <ParaValue>114</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_noise_margin</ParaName>
        <ParaValue>121</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_attenuation</ParaName>
        <ParaValue>142</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_attenuation</ParaName>
        <ParaValue>180</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_power</ParaName>
        <ParaValue>145</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_power</ParaName>
        <ParaValue>72</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Data_path</ParaName>
        <ParaValue>Interleaved</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownInterleavedepth</ParaName>
        <ParaValue>8</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpInterleaveDepth</ParaName>
        <ParaValue>1</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownInterleaveDelay</ParaName>
        <ParaValue>4</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpInterleaveDelay</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownstreamInp</ParaName>
        <ParaValue>20</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpstreamInp</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Showtime_start</ParaName>
        <ParaValue>345600</ParaValue>
    </Instance>
    <Instance>
        <ParaName>tLinkEncapsulationUsed</ParaName>
        <ParaValue>PTM</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownCrc_errors</ParaName>
        <ParaValue>3</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpCrc_errors</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Fec_errors</ParaName>
        <ParaValue>1240</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Atuc_fec_errors</ParaName>
        <ParaValue>185</ParaValue>
    </Instance>
</ajax_response_xml_root>
"""


class AllParametersTests(unittest.TestCase):
    def test_extract_and_parse_all_26_parameters(self):
        root = extract_xml(SAMPLE_ROUTER_XML)
        values = xml_values(root)
        self.assertEqual(values["Status"], "Up")
        self.assertEqual(values["Module_type"], "VDSL2")
        self.assertEqual(values["CurrentProfile"], "17a")
        self.assertEqual(values["Downstream_current_rate"], "109200")
        self.assertEqual(values["Upstream_current_rate"], "42800")
        self.assertEqual(values["Downstream_power"], "145")
        self.assertEqual(values["DownCrc_errors"], "3")
        self.assertEqual(values["Fec_errors"], "1240")
        self.assertEqual(values["Showtime_start"], "345600")

    def test_normalize_to_home_assistant(self):
        root = extract_xml(SAMPLE_ROUTER_XML)
        values = xml_values(root)
        ha_data = normalize_to_ha(values)

        # Check conversion of rates to Mbit/s
        self.assertEqual(ha_data["downstream_sync"], 109.2)
        self.assertEqual(ha_data["upstream_sync"], 42.8)
        self.assertEqual(ha_data["downstream_max"], 118.5)
        self.assertEqual(ha_data["upstream_max"], 46.1)

        # Check SNR and attenuation to dB
        self.assertEqual(ha_data["downstream_snr"], 11.4)
        self.assertEqual(ha_data["upstream_snr"], 12.1)
        self.assertEqual(ha_data["downstream_attenuation"], 14.2)
        self.assertEqual(ha_data["upstream_attenuation"], 18.0)

        # Check power to dBm
        self.assertEqual(ha_data["downstream_power"], 14.5)
        self.assertEqual(ha_data["upstream_power"], 7.2)

        # Check diagnostic integers and strings
        self.assertEqual(ha_data["profile"], "17a")
        self.assertEqual(ha_data["modulation"], "VDSL2")
        self.assertEqual(ha_data["dsl_status"], "Up")
        self.assertEqual(ha_data["data_path"], "Interleaved")
        self.assertEqual(ha_data["showtime"], 345600)
        self.assertEqual(ha_data["downstream_crc"], 3)
        self.assertEqual(ha_data["upstream_crc"], 0)
        self.assertEqual(ha_data["downstream_fec"], 1240)
        self.assertEqual(ha_data["upstream_fec"], 185)
        self.assertEqual(ha_data["downstream_interleave_delay"], 4)
        self.assertEqual(ha_data["downstream_inp"], 2.0)


if __name__ == "__main__":
    unittest.main()
