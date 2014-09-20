#!/usr/bin/env python
'''
Mechwarrior Online Pilot Data Parser v0.00.0001

'''

from HTMLParser import HTMLParser
import requests
import yaml
import calendar
import datetime
import ConfigParser
import sys


LOGIN_URL = 'https://mwomercs.com/do/login'
STATS_URL = 'https://mwomercs.com/profile/stats?type={0}'


class MWOTableParser(HTMLParser):
    '''
    Extend HTMLParser
    '''

    def __init__(self):
        '''
        Init

        '''
        self.reset()
        self._process_data = False
        self._is_tr = False
        self._is_td = False
        self._is_th = False
        self.data_dict = {}
        self._td_count = 0
        self._key_name = ''
        self._values = {}
        self._headings = []

    def handle_starttag(self, tag, attrs):
        '''
        Handle start tags
        '''
        if tag == 'table':
            self._process_data = True
        if tag == 'tr':
            self._is_tr = True
            self._values = {}
        if tag == 'td':
            self._is_td = True
            self._td_count += 1
        if tag == 'th':
            self._is_th = True

    def handle_endtag(self, tag):
        '''
        Reset on ending of tags

        '''
        if tag == 'table':
            self._process_data = False
        if tag == 'tr':
            self._is_tr = False
            if self._td_count > 0:
                self.data_dict.update({self._key_name: self._values})
            self._td_count = 0
        if tag == 'td':
            self._is_td = False
        if tag == 'th':
            self._is_th = False

    def handle_data(self, data):
        '''
        Process the data

        '''
        if self._process_data:
            if self._is_tr and self._is_td:
                if self._td_count == 1:
                    self._key_name = data
                else:
                    self._values.update(
                        {
                            self._headings[self._td_count - 1]: data
                        }
                    )
            if self._is_tr and self._is_th:
                self._headings.append(data)



def parse_config(filename):
    '''
    Load a config file with username, password
    '''
    config_dict = {}
    section = 'Mechwarrior'
    config = ConfigParser.ConfigParser()
    config.read(filename)
    options = config.options(section)
    for option in options:
        config_dict.update({option: config.get(section, option)})
    return config_dict



def parse_type(session, get_str):
    '''
    Parse the particular type of statistic

    '''
    # hack to make base blank for get query
    if get_str == 'base':
        get_str = ''
    request = session.get(
        STATS_URL.format(get_str)
    )
    parser = MWOTableParser()
    parser.feed(str(request.content))
    return parser.data_dict


def main():
    '''
    Main Function
    '''

    config = parse_config('mwostatter.ini')

    login_data = {
        'email': config['email'],
        'password': config['password'],
        'submit': 'login'
    }

    session = requests.session()
    session.post(LOGIN_URL, data=login_data)
    data_dict = {}
    stats_dict = {}
    get_strs = ['base', 'mech', 'weapon', 'pilot', 'map', 'mode']
    for get_str in get_strs:
        stats_dict.update({get_str: parse_type(session, get_str)})
    data_dict = {
        'timestamp': str(
            calendar.timegm(
                datetime.datetime.utcnow().timetuple()
            )
        ),
        'stats': stats_dict
    }

    print yaml.dump(data_dict, default_flow_style=False)


if __name__ == '__main__':
    sys.exit(main())
