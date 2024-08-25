#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.parse
import urllib.request
import uuid
import warnings
from urllib.parse import urlencode  # @UnusedImport
from urllib.request import pathname2url  # @UnusedImport


TIME_ZONE = "GMT"
FORMAT_ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"
FORMAT_RFC_2616 = "%a, %d %b %Y %X GMT"

warnings.filterwarnings("once", category=DeprecationWarning)


def get_sign_string(source, secret):
    h = hmac.new(secret.encode('utf-8'), source.encode('utf-8'), hashlib.sha1)
    signature = base64.encodebytes(h.digest()).strip()
    return signature


def get_signer_name():
    return "HMAC-SHA1"


def get_singer_version():
    return "1.0"


def get_uuid():
    return str(uuid.uuid4())


def get_iso_8061_date():
    return time.strftime(FORMAT_ISO_8601, time.gmtime())


def get_rfc_2616_date():
    return time.strftime(FORMAT_RFC_2616, time.gmtime())


def md5_sum(content):
    return base64.standard_b64encode(hashlib.md5(content).digest())


def percent_encode(encodeStr):
    encodeStr = str(encodeStr)
    if sys.stdin.encoding is None:
        res = urllib.quote(encodeStr.decode('cp936').encode('utf8'), '')
    else:
        res = urllib.quote(
            encodeStr.decode(
                sys.stdin.encoding).encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res


class ArgumentError(Exception):
    pass


class APIError(Exception):
    pass


class DomainNotFoundError(Exception):
    pass


class RecordNotFoundError(Exception):
    pass


class AccessKeyIdNotFound(Exception):
    pass


class SignatureDoesNotMatch(Exception):
    pass

class NoIPv6AddressError(Exception):
    """自定义异常：无IPv6地址"""
    pass

def getIPv6():
    url = "https://6.ipw.cn"

    try:
        # 发送 HTTP GET 请求
        with urllib.request.urlopen(url) as response:
            # 读取响应内容并解码为字符串
            ipv6_address = response.read().decode('utf-8').strip()

            # 检查是否返回了有效的 IPv6 地址
            if ipv6_address:
                return ipv6_address
            else:
                raise NoIPv6AddressError("No IPv6 address found.")

    except urllib.error.URLError as e:
        raise NoIPv6AddressError(f"Network error occurred: {e}")

    except Exception as e:
        raise NoIPv6AddressError(f"An unexpected error occurred: {e}")

def parse_args():
    parser = argparse.ArgumentParser(sys.argv[0])

    parser.add_argument('secret_id', type=str,
                        help='aliyun cloud secret_id')
    parser.add_argument('secret_key', type=str,
                        help='aliyun cloud secret_key')
    parser.add_argument('domain', type=str, help='DDNS domain')
    parser.add_argument('ip', type=str, help='DDNS ip')

    return parser.parse_args()


def __init__():
    pass


# this function will append the necessary parameters for signer process.
# parameters: the orignal parameters
# signer: sha_hmac1 or sha_hmac256
# accessKeyId: this is aliyun_access_key_id
# format: XML or JSON
def __refresh_sign_parameters(
        parameters,
        access_key_id,
        accept_format="JSON"):
    if parameters is None or not isinstance(parameters, dict):
        parameters = dict()
    parameters["Timestamp"] = get_iso_8061_date()
    parameters["SignatureMethod"] = get_signer_name()
    parameters["SignatureVersion"] = get_singer_version()
    parameters["SignatureNonce"] = get_uuid()
    parameters["AccessKeyId"] = access_key_id
    if accept_format is not None:
        parameters["Format"] = accept_format
    return parameters


def __pop_standard_urlencode(query):
    ret = urlencode(query)
    ret = ret.replace('+', '%20')
    ret = ret.replace('*', '%2A')
    ret = ret.replace('%7E', '~')
    return ret


def __compose_string_to_sign(method, queries):
    canonicalized_query_string = ""
    sorted_parameters = sorted(queries.items(), key=lambda queries: queries[0])
    string_to_sign = method + "&%2F&" + \
                     pathname2url(__pop_standard_urlencode(sorted_parameters))

    return string_to_sign


def __get_signature(string_to_sign, secret):
    return get_sign_string(string_to_sign, secret + '&')


def get_signed_url(params, ak, secret, accept_format, method):
    sign_params = __refresh_sign_parameters(params, ak, accept_format)
    string_to_sign = __compose_string_to_sign(method, sign_params)
    signature = __get_signature(string_to_sign, secret)
    sign_params['Signature'] = signature
    url = '/?' + __pop_standard_urlencode(sign_params)
    return url


def main():
    args = parse_args()
    try:
        res = DNSPodUpdater(args.secret_id, args.secret_key).execute(args.domain, args.ip)
        print(res, end='')
    except AccessKeyIdNotFound:
        print('badauth', end='')
    except SignatureDoesNotMatch:
        print('badauth', end='')
    except RecordNotFoundError:
        print('nohost', end='')
    except DomainNotFoundError:
        print('nohost', end='')


class DNSPodUpdater():
    def __init__(self, secret_id, secret_key):
        self.api_sender = DNSPodAPISender(secret_id, secret_key)

    def execute(self, full_domain, ip):
        domain, sub_domain = self._query_domain(full_domain)
        try:
            ipv6_address = getIPv6()
            print(f"IPv6 address is: {ipv6_address}")
            record_id, value = self._query_record(domain, sub_domain, 'AAAA')
            if record_id is not None:
                if value != ipv6_address:
                    self._modify_ip_v6(domain, record_id, sub_domain, ipv6_address)
        except NoIPv6AddressError as e:
            print(f"Error: {e}")

        record_id, value = self._query_record(domain, sub_domain, 'A')
        if record_id is not None:
            if value != ip:
                self._modify_ip(domain, record_id, sub_domain, ip)

                return "good"
            else:
                return "nochg"
        else:
            return "nohost"



    def _query_domain(self, full_domain):
        domain_list = self.api_sender.send({
            'Action': 'DescribeDomains'
        })

        if 'Domain' not in domain_list['Domains']:
            raise APIError('DomainList: {}'.format(domain_list))

        for domain in domain_list['Domains']['Domain']:
            domain_name = domain['DomainName']

            if not full_domain.endswith(domain_name):
                continue

            if domain_name == full_domain:
                sub_domain = '@'
            else:
                sub_domain = full_domain.replace('.{}'.format(domain_name), '')

            return domain_name, sub_domain

        raise DomainNotFoundError(full_domain)

    def _query_record(self, domain, sub_domain, type):
        record_list = self.api_sender.send({
            'Action': 'DescribeDomainRecords',
            'DomainName': domain,
            'RRKeyWord': sub_domain,
            'Type': type
        })

        if 'Record' not in record_list['DomainRecords']:
            raise APIError('RecordList: {}'.format(record_list))

        if len(record_list['DomainRecords']['Record']) != 1:
            raise RecordNotFoundError('sub_domain: {}'.format(sub_domain))

        for record in record_list['DomainRecords']['Record']:
            return record['RecordId'], record['Value']

    def _modify_ip(self, domain, record_id, sub_domain, ip):
        self.api_sender.send({
            'Action': 'UpdateDomainRecord',
            'domain': domain,
            'RecordId': record_id,
            'RR': sub_domain,
            'Type': 'A',
            'Value': ip
        })

    def _modify_ip_v6(self, domain, record_id, sub_domain, ip):
        self.api_sender.send({
            'Action': 'UpdateDomainRecord',
            'domain': domain,
            'RecordId': record_id,
            'RR': sub_domain,
            'Type': 'AAAA',
            'Value': ip
        })


class DNSPodAPISender():
    def __init__(self, secret_id, secret_key):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.url = 'alidns.aliyuncs.com'

    def send(self, params):
        signed_url = get_signed_url(params, self.secret_id, self.secret_key, "JSON", "GET")

        url = 'http://{url}{params}'.format(url=self.url, params=signed_url)
        action = params["Action"]
        headers = {
            'x-sdk-invoke-type': 'common',
            'x-acs-version': '2015-01-09',
            'x-acs-action': action,
            'x-sdk-client': 'python/2.0.0'
        }
        try:
            with urllib.request.urlopen(urllib.request.Request(url=url, headers=headers)) as response:
                return json.loads(response.read())
        except urllib.request.URLError as e:
            res = json.loads(e.read())
            code = res['Code']
            if code == 'InvalidAccessKeyId.NotFound':
                raise AccessKeyIdNotFound
            elif code == 'SignatureDoesNotMatch':
                raise SignatureDoesNotMatch
            else:
                raise SignatureDoesNotMatch


main()
