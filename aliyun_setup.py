import configparser

section_name = 'Aliyun'
conf = '/etc.defaults/ddns_provider.conf'

parser = configparser.ConfigParser()
parser.read(conf)
if section_name not in parser.sections():
    parser.add_section(section_name)

parser.set(section_name, 'modulepath', '/usr/syno/bin/ddns/aliyun.py')
parser.set(section_name, 'queryurl', 'https://www.aliyun.com')

with open(conf, 'w+') as f:
    parser.write(f)
