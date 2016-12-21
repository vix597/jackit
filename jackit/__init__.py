'''
The main game loop
'''

import os
import sys
import marshal
import requests

from deploy import SiteDeployment

class JackitGame:
    '''
    JackIt Game class
    '''

    @staticmethod
    def run():
        '''
        Run the game
        '''
        from jackit.core.engine import GameEngine

        while GameEngine.running:
            GameEngine.update()

        print("Game over {}: ".format(GameEngine.user))
        print("\tScore: ", GameEngine.total_points)
        print("\tDeaths: ", GameEngine.deaths)
        print("\tPlaytime: {0:.2f}s".format(GameEngine.playtime))

        if GameEngine.user is None:
            return

        print("Submitting score...")

        #Super secure (not really...at all)
        try:
            result = {}
            code_obj = marshal.load(open(os.path.join(SiteDeployment.base_path, "gen.dump"), "rb"))

            # pylint: disable=W0122
            exec(code_obj, {
                'user': GameEngine.user,
                'score': GameEngine.total_points,
                'deaths': GameEngine.deaths,
                'playtime': GameEngine.playtime
            }, locals())

            r = requests.post(
                GameEngine.config.leaderboard.submission_url,
                data={
                    'user': GameEngine.user,
                    'score':GameEngine.total_points,
                    'deaths':GameEngine.deaths,
                    'playtime':GameEngine.playtime,
                    'code': result["code"]
                }
            )
            print(r.status_code, r.reason)
        except BaseException as e:
            print(e)
            return
