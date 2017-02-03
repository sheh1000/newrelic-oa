#!/usr/bin/python

import sys
import os
import requests
import socket
import json
import logging
import time

#--------------------------------------------------------------------
class Newrelic_Metrics(object):

    def __init__(self, proxies, nr_licence_key, agent_name, agent_version, guid, 
                 poll_cycle, metrics, hostname):
        self.proxies = proxies
        self.nr_api_url = 'https://platform-api.newrelic.com/platform/v1/metrics'
        self.nr_licence_key = nr_licence_key
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.guid = guid
        self.poll_cycle = poll_cycle
        self.metrics = metrics
        self.hostname = hostname

    def http_request(self, url, proxies, headers, data, timeout):
        """ HTTP request """
        try:
            logger.info("Sending HTTP POST request: %s " % (url), extra={'hostname': hostname})
            encoded_str = json.dumps(data)
            start_timer = time.time()

            if proxies:
                r = requests.post(url,
                                proxies=proxies,
                                headers=headers, 
                                data=encoded_str, 
                                timeout=timeout)
            else:
                r = requests.post(url, headers=headers, data=encoded_str, timeout=timeout)

            response_time = "%.2f" % (time.time() - start_timer)
            if r.status_code == requests.codes.ok:
                logger.info("HTML code: %s" % (r.status_code), extra={'hostname': hostname})
                return True, r.status_code, r.headers, response_time
            else:
                logger.info("\nAn error occurred, status code %s" % (r.status_code), extra={'hostname': hostname})
                return False, r.status_code, r.headers, response_time
        except requests.exceptions.RequestException, e:
            logger.info('\nERROR: Request exception occurred', extra={'hostname': hostname})
            logger.info(e, extra={'hostname': hostname})
            return False, None, None, None, None

    def get_payload(self):
        """ Returns formatted payload """
        agent={}
        agent["host"]=self.hostname
        agent["version"]=self.agent_version
        components_load={}
        components_load["name"]=self.agent_name
        components_load["guid"]=self.guid
        components_load["duration"]=self.poll_cycle
        components_load["metrics"]=self.metrics
        components=[]
        components.append(components_load)
        payload={}
        payload["agent"]=agent
        payload["components"]=components

        for key, value in self.metrics.iteritems():
            logger.info("%s %s" % (key, value), extra={'hostname': hostname})

        return payload

    def newrelic_post_request(self):
        # disable url urllib3 warnings for older python versions
        requests.packages.urllib3.disable_warnings()
        
        payload = self.get_payload()
        logger.info("Payload: \n%s" % payload, extra={'hostname': hostname})
        headers = {"Content-Type": "application/json", 
                   "Accept": "application/json", 
                   "X-License-Key": self.nr_licence_key}
        logger.info("headers: \n%s" % headers, extra={'hostname': hostname})
        (request_status, status_code, headers, response_time) = self.http_request(self.nr_api_url, self.proxies, headers, payload, 10)
        logger.info("HTTP request status:\n %s, \n HTTP code:%s, \n Headers: %s, \n Latency:%s\n\n" % (request_status, 
                                                                                                                 status_code, 
                                                                                                                 headers, 
                                                                                                                 response_time), 
                                                                                                                 extra={'hostname': hostname})


if __name__ == "__main__":
    """ Configure logging settings """ 
    logging.basicConfig(format='%(asctime)s %(message)s', filename='/var/log/newrelic_plugin.log', level=logging.INFO)
    logger = logging.getLogger(__name__)

    """ Take arguments from Robot Framework test """ 
    domain = sys.argv[1]            # cp domain name
    val = sys.argv[2]               # test time. Will be "-1" if failed
    nr_licence_key = sys.argv[3]    # customer New Relic license key

    """  Prepare data before sending to New Relic plugin API """ 
    hostname = socket.gethostname()
    metrics = {}
    metrics["Custom/ControlPanel/%s" % domain]=float(val)
    newrelic_utils = Newrelic_Metrics(
                        proxies={
                                "https":"https://<proxy_ip>:3128"
                                },
                        #proxies=False,
                        nr_licence_key=nr_licence_key, 
                        agent_name="OdinRobotFramework", 
                        agent_version="1.0.0", 
                        guid="OdinMonitoringPlugin", 
                        poll_cycle=60, 
                        metrics=metrics, 
                        hostname=hostname)

    newrelic_utils.newrelic_post_request()
