import pytest
import requests
import json
import logging
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from common.json_checker import check_difference
from test_case import BaseTestCase
from functools import reduce
from api_tests.ban_games import ban_list, skip_list
from db.mysql_connection import MariaDBConnection


log = logging.getLogger(__name__)
log.setLevel('INFO')


broken_db_list = ['american_poker_2',
                  'american_poker_2_mob',
                  'dynamite_bingo',
                  ]
more_than_one_reelset_in_main_game = ['100_monkeys',
                                      '100_monkeys_mob',
                                      'candy_mix',
                                      'candy_mix_mob',
                                      ]
PLAYER_CASH = 'http://wl-beta.dev.dzento.com/api?cm=player_cash&wlid=16395&cash_type=real&type=set&money=10000000'
NGL_ADM = 'https://dcpbot-ods-02.dev.dzento.com/cgi/admservice/admservice.cgi'
COMMAND_SHIFT = '{NGL_CGI}?post=json:%7B"shift": %7B"shifts":"{shift_index}"%7D, "clear": "true", "session": "{' \
                'session}", "command": "deadpool"%7D '
COMMAND_GAMES = '{NGL_ADM}?cm=games&format=xml'
NGL_CGI = 'https://dcpbot-ods-02.dev.dzento.com/cgi/server.cgi'
KEY = 'fe7992d9b4008bda95431f3a548670eb'
CONNECT_URL = '{NGL_CGI}?post=json:%7B"command":"connect","playerguid":"{key}","game":"{game_name}"%7D'
START_URL = '{NGL_CGI}?post=json:%7B"session":"{session}","command":"start"%7D'
RECONNECT_URL = '{NGL_CGI}?post=json:%7B"session":"{session}","command":"reconnect"%7D'
COMMAND_BET = '{NGL_CGI}?post=json:%7B"session":"{session}","command":"bet","game":"{game_name}",{bet_parameters}%7D'


def get_game_name():
    games_list = []
    res = requests.get(COMMAND_GAMES.format(NGL_ADM=NGL_ADM))
    tree = ElementTree.fromstring(res.content)
    for i in tree.iter('title'):
        if i.text not in ban_list:
            games_list.append(i.text)
    return games_list


class TestServer(BaseTestCase):
    test_case_url = 'https://testrail.dzento.com/index.php?/cases/view/173597,' \
                    'https://testrail.dzento.com/index.php?/cases/view/173600'
    not_valid_not = 'NOTVALIDNOT'
    not_game = 'not game'
    not_current = 'not current'
    not_bet = 'not bet'
    not_init = 'not init'
    not_ranges = 'not ranges'
    not_bets = 'not bets'
    
    def set_money(self):
        requests.get(PLAYER_CASH) 

    def response_start(self, one_game_name):
        res_connect = requests.get(CONNECT_URL.format(NGL_CGI=NGL_CGI, key=KEY, game_name=one_game_name)).json()
        session_start = res_connect.get('session')
        res_start = requests.get(START_URL.format(NGL_CGI=NGL_CGI, session=session_start)).json()
        return res_start

    def response_reconnect(self, one_game_name):
        res_connect = requests.get(CONNECT_URL.format(NGL_CGI=NGL_CGI, key=KEY, game_name=one_game_name)).json()
        session_reconnect = res_connect.get('session')
        res_reconnect = requests.get(RECONNECT_URL.format(NGL_CGI=NGL_CGI, session=session_reconnect)).json()
        return res_reconnect

    def _check_if(self, item, message):
        if item != self.not_valid_not:
            return item
        assert False, message

    def _recursive_dict_get(self, keys, res_star):
        return reduce(
            lambda c, k: self._check_if(c.get(k[0], self.not_valid_not), k[1]),
            keys,
            res_star
        )

    @pytest.mark.parametrize('one_game_name', get_game_name())
    def test_start_bet_value(self, one_game_name):
        if one_game_name in skip_list:
            pytest.skip("Skipped because this is Native Game.")
        self.set_money()
        res_star = self.response_start(one_game_name)
        bet_keys = [
            ('game', self.not_game),
            ('current', self.not_current),
            ('bet', self.not_bet)
        ]
        bet = self._recursive_dict_get(bet_keys, res_star)

        bets_keys = [
            ('game', self.not_game),
            ('init', self.not_init),
            ('ranges', self.not_ranges),
            ('bets', self.not_bets)
        ]
        bets = self._recursive_dict_get(bets_keys, res_star)[0][0]
        fail_error = 'bet: {} != bets: {}'

        assert bet == bets, fail_error.format(bet, bets)

    @pytest.mark.parametrize('one_game_name', get_game_name())
    def test_server(self, one_game_name):
        if one_game_name in skip_list:
            pytest.skip("Skipped because this is Native Game.")
        self.set_money()
        res_star = self.response_start(one_game_name).get('game', False)
        res_recon = self.response_reconnect(one_game_name).get('game', False)
        # if not res_recon:
        #     res_recon = res_reconnect.get('data')
        # if not res_star:
        #     res_star = res_start.get('data')
        result = check_difference(res_star, res_recon)
        log.error('{}'.format(json.dumps(result, indent=4, sort_keys=True)))
        bool_result = bool(result)
        assert not bool_result, 'Different response in Start and Reconnect commands'

    def shifter_bet(self, one_game_name, shift_index):
        res_star = self.response_start(one_game_name)
        session = res_star.get('session')
        bet_parameters = ''
        try:
            game = res_star['game']['current']
        except KeyError:
            game = res_star['game']
        for i in game:
            if i == 'lines':
                bet_parameters += '"'
                bet_parameters += i
                bet_parameters += '"'
                bet_parameters += ':'
                bet_parameters += str(game[i])
                bet_parameters += ','
            if i == 'bet':
                bet_parameters += '"'
                bet_parameters += i
                bet_parameters += '"'
                bet_parameters += ':'
                bet_parameters += str(game[i])
                bet_parameters += ','
            if i == 'coin':
                bet_parameters += '"'
                bet_parameters += i
                bet_parameters += '"'
                bet_parameters += ':'
                bet_parameters += str(game[i])
                bet_parameters += ','
            if i == 'multiplier':
                bet_parameters += '"'
                bet_parameters += i
                bet_parameters += '"'
                bet_parameters += ':'
                bet_parameters += str(game[i])
                bet_parameters += ','
        bet_parameters = bet_parameters[:-1]
        requests.get(COMMAND_SHIFT.format(NGL_CGI=NGL_CGI, shift_index=shift_index, session=session)).json()
        bet_req = requests.get(COMMAND_BET.format(NGL_CGI=NGL_CGI, session=session, game_name=one_game_name,
                                                  bet_parameters=bet_parameters)).json()
        return bet_req

    @pytest.mark.parametrize('one_game_name', get_game_name())
    def test_start_shifter(self, one_game_name):
        if one_game_name in skip_list:
            pytest.skip("Skipped because this is Native Game.")
        if one_game_name in broken_db_list:
            pytest.skip("Skipped because MySQL file is not ordinary.")
        if one_game_name in more_than_one_reelset_in_main_game:
            pytest.skip("Skipped because there are more than one reel set in the main game.")
        self.set_money()
        cursor, conn = MariaDBConnection().maria_connection()
        req = "select finfo from games_info where fcm='{one_game_name}';"
        cursor.execute(req.format(one_game_name=one_game_name))
        result = cursor.fetchall()
        conn.close()

        tree = ET.fromstring(result[0][0])
        start_shifts = tree.findall('shifts')
        shifts = []

        for n in start_shifts[0].findall('shift'):
            symbols = n.attrib.get('symbols')
            shifts.append(symbols)

        bet_req_with_shifter = []
        for i in shifts:
            try:
                bet_req_with_shifter.append(self.shifter_bet(one_game_name, i)['game']['spin']['symbols'])
            except KeyError:
                bet_req_with_shifter.append(self.shifter_bet(one_game_name, i)['game']['symbols'])
        i = len(shifts)
        while i > 0:
            try:
                start_symbols = (self.response_start(one_game_name)['game']['spin']['symbols'])
            except KeyError:
                start_symbols = (self.response_start(one_game_name)['game']['symbols'])
            fail = 'There is no {start_symbols} in {bet_req_with_shifter}'
            if start_symbols in bet_req_with_shifter:
                i -= 1
            else:
                assert start_symbols in bet_req_with_shifter, fail.format(start_symbols=start_symbols,
                                                                          bet_req_with_shifter=bet_req_with_shifter)
